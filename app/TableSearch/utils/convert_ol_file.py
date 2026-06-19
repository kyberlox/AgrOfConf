import asyncio
import base64
from collections import defaultdict
import io
import os
import tempfile
from pathlib import Path
from typing import List, Dict

from app.TableSearch.utils.dm_search import ensure_dm_exists, get_full_search_from_dm
import fitz  # PyMuPDF
import pypandoc
from PIL import Image
from fastapi import UploadFile
from fastapi import HTTPException
from sqlalchemy import text


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
        raise HTTPException(status_code=500, detail=str(e))
    

async def convert_file_to_jpeg_content(file: UploadFile) -> List[Dict]:
    """Конвертирует UploadFile → JPEG-изображения (base64) для OpenAI."""
    file_bytes = await file.read()
    await file.seek(0)
    ext = Path(file.filename or "").suffix.lower()
    content = []

    # 1. Изображения → JPEG
    if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        content.append(_make_jpeg_item(buf.getvalue()))
        return content

    # 2. PDF → сразу берём байты
    if ext == ".pdf":
        pdf_bytes = file_bytes
    # 3. Документы (docx, odt, rtf, md, html) → PDF через pandoc + временный файл
    elif ext in {".md", ".html"}:
        pdf_bytes = await _convert_to_pdf_with_tempfile(file_bytes, ext)
    elif ext in {".docx", ".odt", ".rtf"}: 
        pdf_bytes = await convert_docx_to_pdf_libreoffice(file_bytes, ext)
    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")

    # Рендерим страницы PDF в JPEG
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Ошибка открытия PDF: {e}")

    for page in doc:
        pix = page.get_pixmap(dpi=300)
        content.append(_make_jpeg_item(pix.tobytes("jpeg")))
    doc.close()
    return content


def _make_jpeg_item(jpeg_bytes: bytes) -> Dict:
    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
    }


async def _convert_to_pdf_with_tempfile(file_bytes: bytes, ext: str) -> bytes:
    """Конвертация docx/odt/... → PDF через pypandoc во временный файл."""
    # Создаём временный файл для результата
    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)  # Закрываем дескриптор, файл пока остаётся
    
    try:
        # pypandoc 1.17 сохраняет PDF в файл, указанный в outputfile
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
        # Читаем полученный PDF
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
    finally:
        # Удаляем временный файл
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return pdf_bytes

async def convert_docx_to_pdf_libreoffice(file_bytes: bytes, extension: str) -> bytes:
    """Конвертирует документ (docx, odt, rtf) в PDF с помощью LibreOffice."""
    # Создаём временный каталог (чтобы избежать конфликтов имён)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_file = tmpdir / f"input{extension}"    # сохраняем исходный файл
        input_file.write_bytes(file_bytes)

        # Запускаем LibreOffice в headless-режиме
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

        output_pdf = tmpdir / f"input.pdf"
        if not output_pdf.exists():
            raise FileNotFoundError("PDF не был создан")

        return output_pdf.read_bytes()