# app/products/router/tkp_generation.py
import os
import re
from io import BytesIO
from typing import Optional
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
from datetime import datetime
from ..utils.router_utils import to_sql_name_lat

from app.StatisticsService.utils.deps import build_statistic_data
from app.UserService.utils.auth_utils import get_user_id_by_session_id
from app.StatisticsService.router.selection_router import get_selection_router

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

@router.post("/create_tkp")
async def tkp_generation(
        file_id: int,
        product_id: int,
        user_dict: dict,
        db: AsyncSession = Depends(get_db),
        user_id: Optional[int] = Depends(get_user_id_by_session_id),
        statistic_router = Depends(get_selection_router),
):
    try:
        # Получаем файл из БД по id
        stmt = select(TKP).where(TKP.id == file_id)
        result = await db.execute(stmt)
        file_info = result.scalar_one_or_none()
        if not file_info:
            raise HTTPException(status_code=404, detail="Файл не найден")
        template_path = file_info.file
        contact_info = ["Имя агента", "Маркировка"]
        if not all(key in user_dict for key in contact_info):
            raise HTTPException(status_code=400, detail="Не все обязательные поля заполнены")

        filename = f"TKP_{to_sql_name_lat(user_dict['Имя агента'])}_{to_sql_name_lat(user_dict['Маркировка'])}"

        # Сохраняем статистику
        stat_info = await build_statistic_data(db, user_id, product_id)
        stat_info['parameters'] = user_dict
        is_dump = await statistic_router.save_recognition(stat_info)

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
                    "Content-Disposition": f'attachment; filename="{filename}.docx"'
                }
            )

        elif template_path.endswith(".xlsx"):
            workbook = load_workbook(template_path)

            for sheet in workbook.worksheets:
                for row in sheet.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, str):
                            for key, value in user_dict.items():
                                pattern = re.compile(r'\{\{\s*' + re.escape(key) + r'\s*\}\}')
                                cell.value = pattern.sub(str(value), cell.value)

            result_stream = BytesIO()
            workbook.save(result_stream)
            result_stream.seek(0)

            return StreamingResponse(
                result_stream,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.xlsx"'
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Неподдерживаемый формат для файла"
            )
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации ТКП: {str(e)}" 
        )


@router.post("/add", response_model=TKPResponse, status_code=201, description="Добавление шаблона ТКП.")
async def add_tkp_file(
        product_id: int = Form(...),
        filename: str = Form(...),
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    try:
        validate_file(file)
        safe_filename = f"{uuid4().hex}{Path(file.filename).suffix.lower()}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        file_url = f"/api/files/tkp_files/{safe_filename}"

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
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении ТКП: {str(e)}")


@router.get("/get_tkp_of_product/{product_id}", response_model=list[TKPResponse], description="Выведение всех ТКП продукта из БД.")
async def get_tkp_file(
        product_id: int,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TKP)
        .where(TKP.product_id == product_id)
        .offset(skip)
        .limit(limit)
    )

    samples = result.scalars().all()

    # if not samples:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="TKP templates not found"
    #     )

    return samples


@router.delete("/delete_all_tkp_of_product/{product_id}", description="Удаление шаблона ТКП.")
async def delete_tkp_file(
        product_id: int,
        db: AsyncSession = Depends(get_db)
):
    try:
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
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления шаблонов ТКП продукта с id = {product_id}: {str(e)}")

@router.delete("/delete/{tkp_id}", description="Удаление шаблона ТКП.")
async def delete_tkp_file(
        tkp_id: int,
        db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(TKP).where(TKP.id == tkp_id))
        sample = result.scalar_one_or_none()

        if sample is None:
            return HTTPException(status_code=404, detail="TKP template not found")

        if sample.file is not None and sample.file != "" and os.path.exists(sample.file):
            os.remove(sample.file)

        await db.delete(sample)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления шаблона ТКП: {str(e)}")