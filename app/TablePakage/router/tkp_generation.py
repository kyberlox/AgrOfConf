# app/products/router/tkp_generation.py
import os
import re
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import load_workbook
from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage

from app.StatisticsService.router.selection_router import get_selection_router
from app.StatisticsService.utils.deps import build_statistic_data
from app.UserService.utils.auth_utils import get_user_id_by_session_id

from ..model.database import get_db
from ..model.tkp import TKP
from ..schema.tkp import TKPResponse
from ..utils.kir_param_to_latin import KEY_MAPPING
from ..utils.router_utils import to_sql_name_lat

router = APIRouter(prefix="/tkp_generation", tags=["TKP"])

UPLOAD_DIR = "./static/tkp_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".docx", ".xlsx"}
PRICE_PARAMS = {"Цена /шт. руб без НДС", "Цена /шт. руб с НДС 22%"}
PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([^}]+)\s*\}\}")
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ────────────────────────────── Вспомогательные функции ──────────────────────────────

def validate_file(file: UploadFile) -> None:
    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension. Allowed: .docx, .xlsx")


async def convert_data(user_dict: dict, db_info: dict) -> dict:
    date = datetime.strptime(db_info["date_search"], "%d.%m.%Y %H:%M:%S").strftime("%d.%m.%Y")
    user_dict.update({
        "дата": date,
        "ТКС": user_dict["id"],
        "адрес_исполнителя": db_info["user_work_city"],
        "телефон_исполнителя": db_info["user_work_phone"],
        "email_исполнителя": db_info["user_email"],
        "фио_исполнителя": db_info["user_fio"],
        "должность_исполнителя": db_info["user_work_position"],
    })
    return user_dict


async def get_template(db: AsyncSession, file_id: int) -> TKP:
    file_info = (await db.execute(select(TKP).where(TKP.id == file_id))).scalar_one_or_none()
    if not file_info:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return file_info


async def save_statistic(db, statistic_router, user_id, product_id, parameters) -> tuple[dict, object]:
    stat_info = await build_statistic_data(db, user_id, product_id)
    stat_info["parameters"] = parameters
    stat_info["document_number"] = await statistic_router.get_number_document(user_id) + 1
    is_dump = await statistic_router.save_selection(stat_info)
    return stat_info, is_dump


async def find_drawing_path(db: AsyncSession, product_id: int, marking: Optional[str]) -> Optional[str]:
    if not marking:
        return None
    row = await db.execute(
        text(
            "SELECT file_path FROM parameter_files "
            "WHERE product_id = :pid AND name ILIKE :pattern LIMIT 1"
        ),
        {"pid": product_id, "pattern": f"%{marking[:5]}%"},
    )
    return row.scalar_one_or_none()


def format_value(param: str, value: Union[int, float, str]) -> Union[int, float, str]:
    """Число → строка с запятой; цены фиксируются с двумя знаками."""
    if isinstance(value, (int, float)):
        return str(value).replace(".", ",")
    if not isinstance(value, str):
        return value
    try:
        number = float(value.strip())
        formatted = f"{number:.2f}" if param in PRICE_PARAMS else (
            int(number) if number % 1 == 0 else number
        )
        return str(formatted).replace(".", ",")
    except ValueError:
        return value


def to_latin(user_dict: dict, *, skip_placeholder: bool = False) -> dict:
    """Переводит ключи в латиницу по KEY_MAPPING и нормализует значения."""
    result = {}
    for param, value in user_dict.items():
        key = KEY_MAPPING.get(param)
        if not key:
            continue
        if skip_placeholder and isinstance(value, str) and "Заполните" in value:
            continue
        result[key] = format_value(param, value)
    return result


def load_drawing(doc: DocxTemplate, path: str) -> InlineImage:
    """Читает чертёж, приводит к RGB/96dpi и оборачивает в InlineImage для шаблона."""
    with open(path, "rb") as f:
        image = Image.open(BytesIO(f.read()))
    if image.mode != "RGB":
        image = image.convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="PNG", dpi=(96, 96))
    buffer.seek(0)
    return InlineImage(doc, buffer, width=Mm(120))


def render_docx(template_path: str, context: dict, drawing_path: Optional[str] = None) -> BytesIO:
    doc = DocxTemplate(template_path)
    if drawing_path:
        context[KEY_MAPPING["Чертеж"]] = load_drawing(doc, drawing_path)
    doc.render(context)
    stream = BytesIO()
    doc.save(stream)
    stream.seek(0)
    return stream


def render_xlsx(template_path: str, context: dict) -> BytesIO:
    workbook = load_workbook(template_path, data_only=True)
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    cell.value = PLACEHOLDER_PATTERN.sub(
                        lambda match: str(context.get(match.group(1).strip(), "")),
                        cell.value,
                    )
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream


def file_response(stream: BytesIO, media_type: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ────────────────────────────── Эндпоинты ──────────────────────────────

@router.post("/create_tkp")
async def tkp_generation(
    file_id: int,
    product_id: int,
    user_dict: dict,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = Depends(get_user_id_by_session_id),
    statistic_router=Depends(get_selection_router),
):
    try:
        template = await get_template(db, file_id)
        if "Маркировка" not in user_dict:
            raise HTTPException(status_code=400, detail="Не все обязательные поля заполнены")

        stat_info, is_dump = await save_statistic(db, statistic_router, user_id, product_id, user_dict)

        user_dict["id"] = is_dump.data["elastic_response"].get("_id")
        user_dict = await convert_data(user_dict, stat_info)
        user_dict["document_number"] = is_dump.data["elastic_response"].get("document_number")

        drawing_path = await find_drawing_path(db, product_id, user_dict.get("Маркировка"))
        filename = (
            f"TKP+TO_{to_sql_name_lat(user_dict.get('ФИО Заказчика', ''))}"
            f"_{to_sql_name_lat(user_dict['Маркировка'])}_{user_dict.get('id', '')}"
        )

        if template.file.endswith(".docx"):
            context = to_latin(user_dict, skip_placeholder=True)
            return file_response(render_docx(template.file, context, drawing_path), DOCX_MEDIA_TYPE, f"{filename}.docx")
        if template.file.endswith(".xlsx"):
            context = to_latin(user_dict)
            return file_response(render_xlsx(template.file, context), XLSX_MEDIA_TYPE, f"{filename}.xlsx")
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат для файла")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации ТКП: {str(e)}")


@router.post("/create_history_tkp", status_code=201, description="Создание ТКП из истории")
async def create_tkp_from_history(
    file_id: int,
    node_id: Union[int, str],
    db: AsyncSession = Depends(get_db),
    statistic_router=Depends(get_selection_router),
):
    try:
        user_history = await statistic_router.get_selection_by_id(node_id)
        if not user_history:
            raise HTTPException(status_code=404, detail="История не найдена")

        template = await get_template(db, file_id)
        user_dict = deepcopy(user_history["parameters"])
        user_dict["id"] = node_id
        user_dict = await convert_data(user_dict, user_history)

        filename = f"TKP_{to_sql_name_lat(user_dict['Имя агента'])}_{to_sql_name_lat(user_dict['Маркировка'])}"

        if template.file.endswith(".docx"):
            return file_response(render_docx(template.file, user_dict), DOCX_MEDIA_TYPE, f"{filename}.docx")
        if template.file.endswith(".xlsx"):
            return file_response(render_xlsx(template.file, user_dict), XLSX_MEDIA_TYPE, f"{filename}.xlsx")
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат для файла")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении истории: {str(e)}")


@router.post("/add", response_model=TKPResponse, status_code=201, description="Добавление шаблона ТКП.")
async def add_tkp_file(
    product_id: int = Form(...),
    filename: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        validate_file(file)
        safe_filename = f"{uuid4().hex}{Path(file.filename).suffix.lower()}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        tkp_sample = TKP(
            name=filename,
            file=file_path,
            file_url=f"/files/tkp_files/{safe_filename}",
            product_id=product_id,
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
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TKP)
        .where(TKP.product_id == product_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.delete("/delete_all_tkp_of_product/{product_id}", description="Удаление шаблона ТКП.")
async def delete_tkp_file(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(TKP).where(TKP.product_id == product_id))
        samples = result.scalars().all()

        if not samples:
            raise HTTPException(status_code=404, detail="TKP templates not found")

        for sample in samples:
            if sample.file is not None and sample.file != "" and os.path.exists(sample.file):
                os.remove(sample.file)
            await db.delete(sample)
        await db.commit()
        return {"detail": "TKP templates deleted successfully", "deleted_count": len(samples)}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления шаблонов ТКП продукта с id = {product_id}: {str(e)}")


@router.delete("/delete/{tkp_id}", description="Удаление шаблона ТКП.")
async def delete_tkp_file(
    tkp_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(TKP).where(TKP.id == tkp_id))
        sample = result.scalar_one_or_none()

        if sample is None:
            raise HTTPException(status_code=404, detail="TKP template not found")

        if sample.file is not None and sample.file != "" and os.path.exists(sample.file):
            os.remove(sample.file)

        await db.delete(sample)
        await db.commit()
        return True
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления шаблона ТКП: {str(e)}")