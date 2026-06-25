# app/products/router/tkp_generation.py
import os

from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, Depends, File, Form
from docxtpl import DocxTemplate
from fastapi.responses import StreamingResponse
from openpyxl import load_workbook
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..model.database import get_db
from ..model.tkp import TKP
from ..schema.tkp import TKPResponse

router = APIRouter(prefix="/tkp_generation", tags=["TKP"])

UPLOAD_DIR = "./static/tkp_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Настройки
ALLOWED_EXTENSIONS = {".docx", ".xlsx"}


def validate_file(file: UploadFile) -> None:
    # Проверка расширения
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension. Allowed: .docx, .xlsx")


# === TKP Generation Endpoints ===

@router.post("/")
async def tkp_generation(
        template_path: str,
        user_dict: dict
):
    if template_path.endswith(".docx"):
        doc = DocxTemplate(template_path)

        doc.render(user_dict)

        result_stream = BytesIO()
        doc.save(result_stream)
        result_stream.seek(0)

        return StreamingResponse(
            result_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": 'attachment; filename="generated_tkp.docx"'
            }
        )

    elif template_path.endswith(".xlsx"):
        workbook = load_workbook(template_path)

        for sheet in workbook.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str):
                        for key, value in user_dict.items():
                            placeholder = "{{ " + key + " }}"
                            cell.value = cell.value.replace(placeholder, str(value))

        result_stream = BytesIO()
        workbook.save(result_stream)
        result_stream.seek(0)

        return StreamingResponse(
            result_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": 'attachment; filename="generated_tkp.xlsx"'
            }
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат для файла"
        )


@router.post("/add", response_model=TKPResponse, status_code=201, description="Добавление шаблона ТКП.")
async def add_tkp_file(
        product_id: int = Form(...),
        filename: str = Form(...),
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    validate_file(file)
    safe_filename = f"{uuid4().hex}{Path(file.filename).suffix.lower()}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    file_url = f"/api/files/tkp/{safe_filename}"

    tkp_sample = TKP(
        name=filename,
        file=file_path,
        file_url=file_url,
        product_id=product_id
    )

    db.add(tkp_sample)
    await db.commit()
    await db.refresh(tkp_sample)

    return tkp_sample


@router.delete("/{product_id}", description="Удаление шаблона ТКП.")
async def delete_tkp_file(
        product_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(TKP).where(TKP.product_id == product_id))
    samples = result.scalars().all()

    if not samples:
        return HTTPException(status_code=404, detail="TKP templates not found")

    for sample in samples:
        if sample.file is not None and sample.file != "" and os.path.exists(sample.file):
            os.remove(sample.file)

        await db.delete(sample)
    await db.commit()
    return {
        "detail": "TKP templates deleted successfully",
        "deleted_count": len(samples)
    }
