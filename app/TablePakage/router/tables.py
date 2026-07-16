# app/products/router/tables.py
import os
import tempfile

from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, File, HTTPException
from fastapi import UploadFile

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import pandas as pd

from ..model.database import get_db
from ..utils.db_utils import create_table
from ..utils.router_utils import to_sql_name_kir, to_sql_name_lat
from .parameter_values import mark_datamart_dirty

import io

import re

router = APIRouter(prefix="/tables", tags=["Tables"])


def normalize_column_name(value):
    return str(value).replace("\xa0", " ").strip()


# === Table Schema Endpoints ===


@router.post("/upload_xlsx", description="Импорт параметров из XLSX с авто-синхронизацией")
async def upload_xlsx(
        product_id: int,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    # Получаем продукт
    product_result = await db.execute(
        text("SELECT name FROM products WHERE id = :id"),
        {"id": product_id}
    )
    product_name = product_result.scalar_one_or_none()

    if product_name is None:
        raise HTTPException(status_code=404, detail="Продукция не найдена")

    filename_without_ext = os.path.splitext(file.filename)[0]

    table_name = f"{to_sql_name_lat(filename_without_ext)}"

    # Создаём таблицу если нет
    await create_table(db, table_name)

    # Читаем Excel
    print("Файл называется: ", file.filename)
    print()

    # Читаем Excel с обработкой ошибок
    contents = await file.read()

    try:
        # Пробуем прочитать с openpyxl (основной движок)
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
    except ValueError as e:
        if "Value must be one of" in str(e):
            # Если проблема со стилями — пробуем xlrd (для старых .xls)
            try:
                df = pd.read_excel(io.BytesIO(contents), engine='xlrd')
            except Exception as xlrd_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл содержит некорректные стили Excel. Не удалось прочитать ни openpyxl, ни xlrd: {xlrd_error}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка чтения Excel файла: {e}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Не удалось прочитать Excel файл: {e}"
        )

    df = df.where(pd.notnull(df), None)

    # Убираем пробелы/переносы/табы по краям названий колонок и неразрывные пробелы из Excel
    df.columns = [
        normalize_column_name(col)
        for col in df.columns
    ]

    if df.empty:
        # Удаляем старую таблицу
        await db.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

        # Создаём пустую таблицу заново
        await create_table(db, table_name)

        # Удаляем параметры из parameter_schemas этой таблицы
        await db.execute(
            text("""
                   DELETE FROM parameter_schemas
                   WHERE table_name = :table_name
               """),
            {"table_name": table_name}
        )

        await mark_datamart_dirty(db, product_id)

        await db.commit()

        return {
            "table": table_name,
            "rows": 0,
            "columns": [],
            "message": "Таблица очищена"
        }

    # Excel → SQL имена
    excel_map = {
        to_sql_name_lat(col): col
        for col in df.columns
        if col.lower() != "id"
    }
    excel_columns_ordered = [
        to_sql_name_lat(col)
        for col in df.columns
        if col.lower() != "id"
    ]

    excel_columns_set = set(excel_columns_ordered)

    # Получаем колонки БД
    result = await db.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
              AND column_name != 'id'
        """),
        {"table_name": table_name}
    )
    db_columns = {row[0] for row in result.fetchall()}

    # Удаляем старую таблицу файла
    await db.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

    # Создаём таблицу заново
    columns_sql = ", ".join(f'"{col}" TEXT' for col in excel_columns_ordered)

    await db.execute(text(f"""
        CREATE TABLE "{table_name}" (
            id SERIAL PRIMARY KEY,
            {columns_sql}
        )
    """))

    # Удаляем старые schema этого файла
    await db.execute(
        text("""
            DELETE FROM parameter_schemas
            WHERE table_name = :table_name
        """),
        {"table_name": table_name}
    )

    # Добавляем заново в правильном порядке
    for col in excel_columns_ordered:
        await db.execute(
            text("""
                    INSERT INTO parameter_schemas (
                        name,
                        transliterated_name,
                        type,
                        table_name,
                        product_id
                    )
                    VALUES (
                        :name,
                        :transliterated_name,
                        'Table',
                        :table_name,
                        :product_id
                    )
                """),
            {
                "name": excel_map[col],
                "transliterated_name": col,
                "table_name": table_name,
                "product_id": product_id
            }
        )
    await db.execute(text("""
            UPDATE parameter_schemas
            SET sort = id
            WHERE product_id = :product_id
              AND sort IS NULL
        """), {"product_id": product_id})

    await db.commit()

    # Делаем вставку в бд
    columns_sql = ", ".join(f'"{col}"' for col in excel_columns_ordered)
    values_sql = ", ".join(f":{col}" for col in excel_columns_ordered)

    insert_sql = text(f"""
            INSERT INTO "{table_name}" ({columns_sql})
            VALUES ({values_sql})
        """)

    rows = [
        {
            col: str(record[excel_map[col]]) if record[excel_map[col]] is not None else None
            for col in excel_columns_ordered
        }
        for record in df.to_dict(orient="records")
    ]

    await db.execute(insert_sql, rows)

    # Обновляем витрину datamart
    await mark_datamart_dirty(db, product_id)

    await db.commit()

    return {
        "table": table_name,
        "rows": len(df),
        "columns": list(excel_columns_ordered)
    }


@router.post("/download_xlsx", description="Выгрузка параметров из БД в XLSX.")
async def download_xlsx(
        product_id: int,
        db: AsyncSession = Depends(get_db)
):
    # Получаем product_name
    product_result = await db.execute(
        text("SELECT name FROM products WHERE id = :id"),
        {"id": product_id}
    )
    product_name = product_result.scalar_one_or_none()

    if product_name is None:
        raise HTTPException(status_code=404, detail="Продукция не найдена")

    # Получаем все таблицы, которые относятся к этому продукту
    tables_result = await db.execute(
        text("""
                SELECT DISTINCT table_name
                FROM parameter_schemas
                WHERE product_id = :product_id
                  AND type = 'Table'
                  AND table_name IS NOT NULL
                ORDER BY table_name
            """),
        {"product_id": product_id}
    )

    table_names = [row[0] for row in tables_result.fetchall()]

    if not table_names:
        raise HTTPException(
            status_code=404,
            detail="У этой продукции нет загруженных таблиц"
        )

    tmp_dir = tempfile.gettempdir()
    file_path = os.path.join(
        tmp_dir,
        f"{to_sql_name_lat(product_name)}_tables.xlsx"
    )

    SYSTEM_COLUMNS = {"id"}

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        has_data = False

        for table_name in table_names:
            # Проверяем, что физическая таблица существует
            exists = await db.execute(
                text("""
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_name = :table_name
                        )
                    """),
                {"table_name": table_name}
            )

            if not exists.scalar():
                continue

            # Получаем данные таблицы
            result = await db.execute(
                text(f'SELECT * FROM "{table_name}" ORDER BY id')
            )

            rows = result.fetchall()
            columns = result.keys()

            if not rows:
                continue

            df = pd.DataFrame(rows, columns=columns)

            # Названия колонок берём из parameter_schemas кириллицей
            columns_result = await db.execute(
                text("""
                        SELECT name, transliterated_name
                        FROM parameter_schemas
                        WHERE product_id = :product_id
                          AND table_name = :table_name
                          AND type = 'Table'
                        ORDER BY COALESCE(sort, id), id
                    """),
                {
                    "product_id": product_id,
                    "table_name": table_name
                }
            )

            schema_columns = columns_result.mappings().all()

            column_name_map = {
                item["transliterated_name"]: item["name"]
                for item in schema_columns
            }

            df.columns = [
                col if col in SYSTEM_COLUMNS else column_name_map.get(col, col)
                for col in df.columns
            ]

            # Excel ограничивает длину названия листа 31 символом
            sheet_name = table_name[:31]

            df.to_excel(
                writer,
                index=False,
                sheet_name=sheet_name
            )

            has_data = True

        if not has_data:
            raise HTTPException(
                status_code=400,
                detail="Все таблицы продукта пустые или не найдены"
            )

    return FileResponse(
        path=file_path,
        filename=f"{to_sql_name_lat(product_name)}_tables.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Access-Control-Expose-Headers": "Content-Disposition"}
    )


@router.delete(
    "/{product_id}/{table_name}",
    description="Удаление таблицы продукта из БД по названию."
)
async def delete_table(
        product_id: int,
        table_name: str,
        db: AsyncSession = Depends(get_db)
):
    # Разрешаем только безопасные SQL-имена, создаваемые to_sql_name_lat
    if not re.fullmatch(r"[a-zA-Z0-9_]+", table_name):
        raise HTTPException(
            status_code=400,
            detail="Некорректное название таблицы"
        )

    # Проверяем существование продукта
    product_result = await db.execute(
        text("""
            SELECT id
            FROM products
            WHERE id = :product_id
        """),
        {"product_id": product_id}
    )

    if product_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Продукция не найдена"
        )

    # Проверяем, что таблица действительно относится к этому продукту
    schema_result = await db.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM parameter_schemas
                WHERE product_id = :product_id
                  AND table_name = :table_name
                  AND type = 'Table'
            )
        """),
        {
            "product_id": product_id,
            "table_name": table_name
        }
    )

    if not schema_result.scalar():
        raise HTTPException(
            status_code=404,
            detail="Таблица не найдена у выбранной продукции"
        )

    # Проверяем наличие самой физической SQL-таблицы
    physical_table_result = await db.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_name = :table_name
            )
        """),
        {"table_name": table_name}
    )

    physical_table_exists = physical_table_result.scalar()

    try:
        # Удаляем физическую SQL-таблицу
        if physical_table_exists:
            await db.execute(
                text(f'DROP TABLE "{table_name}" CASCADE')
            )

        # Удаляем описания всех колонок этой таблицы
        await db.execute(
            text("""
                DELETE FROM parameter_schemas
                WHERE product_id = :product_id
                  AND table_name = :table_name
            """),
            {
                "product_id": product_id,
                "table_name": table_name
            }
        )

        # Сообщаем, что витрину продукта нужно перестроить
        await mark_datamart_dirty(
            db=db,
            product_id=product_id
        )

        await db.commit()

    except Exception as error:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка удаления таблицы: {error}"
        )

    return {
        "product_id": product_id,
        "table_name": table_name,
        "physical_table_deleted": bool(physical_table_exists),
        "message": f"Таблица {table_name} удалена"
    }
