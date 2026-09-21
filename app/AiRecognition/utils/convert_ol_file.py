import asyncio
import base64
from dataclasses import dataclass, field
from io import BytesIO
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF
import pypandoc
from PIL import Image
from fastapi import UploadFile, HTTPException
from sqlalchemy import text

from app.TableSearch.utils.dm_search import ensure_dm_exists, get_full_search_from_dm


@dataclass
class Page:
    """Одна страница документа, подготовленная для распознавания.

    - ``jpeg_bytes`` — JPEG-кодек страницы (для локального OCR);
    - ``base64_url`` — data-URL для vision-моделей;
    - ``width``/``height`` — фактические размеры JPEG-изображения в пикселях
      (нужны для пересчёта координат OCR и оверлеев на фронте);
    - ``item`` — готовый блок content для OpenAI (image_url).
    """
    jpeg_bytes: bytes
    base64_url: str
    width: int
    height: int
    index: int = 0

    @property
    def item(self) -> Dict:
        return {
            "type": "image_url",
            "image_url": {"url": self.base64_url}
        }


async def get_params_and_values_of_product(db, product_id):
    try:
        product_name_result = await db.execute(
            text("""
                SELECT name
                FROM products
                WHERE id = :product_id
            """),
            {"product_id": product_id}
        )

        product_name = product_name_result.scalar_one_or_none()

        if product_name is None:
            raise HTTPException(status_code=404, detail="Продукция не найдена")

        schema_result = await db.execute(
            text("""
                SELECT
                    id,
                    name,
                    transliterated_name,
                    description,
                    type,
                    measuring_unit,
                    table_name,
                    visibility,
                    required_type,
                    sort
                FROM parameter_schemas
                WHERE product_id = :product_id
                AND type = 'Table'
                AND table_name IS NOT NULL
                ORDER BY
                    COALESCE(sort, id),
                    id
            """),
            {"product_id": product_id}
        )

        full_info = schema_result.mappings().all()

        if not full_info:
            raise HTTPException(status_code=404, detail="Параметры не найдены")
        
        await ensure_dm_exists(db, product_id)
        
        full_value_parameters, full_matched_rows = await get_full_search_from_dm(
            db=db,
            product_id=product_id,
        )
        
        result = {item['name']: full_value_parameters[item['name']] for item in full_info}

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении параметров и их значений: {e}")


async def convert_file_to_pages(file: UploadFile, dpi: int = 300) -> List[Page]:
    """Конвертирует UploadFile → список ``Page`` (JPEG-страницы + размеры).

    Основная функция конвейера: результат используется и локальным OCR,
    и (в фолбэке) vision-моделью, поэтому координаты и картинки всегда
    соответствуют друг другу.
    """
    file_bytes = await file.read()
    await file.seek(0)
    ext = Path(file.filename or "").suffix.lower()

    # 1. Одиночное изображение → одна "страница"
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}:
        img = Image.open(BytesIO(file_bytes))
        if img.mode in ("RGBA", "P", "LA", "CMYK"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        jpeg = buf.getvalue()
        w, h = img.size
        return [_make_page(jpeg, w, h, index=0)]

    # 2. PDF → сразу берём байты
    if ext == ".pdf":
        pdf_bytes = file_bytes
    # 3. Документы (md, html) → PDF через pandoc
    elif ext in {".md", ".html"}:
        pdf_bytes = await _convert_to_pdf_with_tempfile(file_bytes, ext)
    # 4. Документы (docx, odt, rtf) → PDF через LibreOffice
    elif ext in {".docx", ".odt", ".rtf"}:
        pdf_bytes = await convert_docx_to_pdf_libreoffice(file_bytes, ext)
    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")

    # Рендерим страницы PDF в JPEG (300 DPI по умолчанию)
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Ошибка открытия PDF: {e}")

    pages: List[Page] = []
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            jpeg = pix.tobytes("jpeg")
            pages.append(_make_page(jpeg, pix.width, pix.height, index=i))
    finally:
        doc.close()
    return pages


def _make_page(jpeg_bytes: bytes, width: int, height: int, index: int) -> Page:
    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    return Page(
        jpeg_bytes=jpeg_bytes,
        base64_url=f"data:image/jpeg;base64,{b64}",
        width=width,
        height=height,
        index=index,
    )


async def convert_file_to_jpeg_content(file: UploadFile) -> List[Dict]:
    """Совместимая обёртка: только OpenAI-контент (для vision-фолбэка)."""
    pages = await convert_file_to_pages(file)
    return [p.item for p in pages]


async def _convert_to_pdf_with_tempfile(file_bytes: bytes, ext: str) -> bytes:
    """Конвертация md/html → PDF через pypandoc во временный файл."""
    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    try:
        pypandoc.convert_text(
            source=file_bytes,
            to="pdf",
            format=ext[1:],
            outputfile=tmp_path,
            extra_args=[
                '--pdf-engine=weasyprint',
                '-V', 'geometry:margin=1in'
            ]
        )
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return pdf_bytes


async def convert_docx_to_pdf_libreoffice(file_bytes: bytes, extension: str) -> bytes:
    """Конвертирует документ (docx, odt, rtf) в PDF с помощью LibreOffice."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_file = tmpdir / f"input{extension}"
        input_file.write_bytes(file_bytes)

        cmd = [
            "soffice",
            "--headless",
            "--norestore",
            "--convert-to", "pdf",
            "--outdir", str(tmpdir),
            str(input_file)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"LibreOffice ошибка: {stderr.decode()}")

        output_pdf = tmpdir / "input.pdf"
        if not output_pdf.exists():
            raise FileNotFoundError("PDF не был создан")

        return output_pdf.read_bytes()