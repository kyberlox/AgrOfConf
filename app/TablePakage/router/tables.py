# app/products/router/tables.py
import os
import tempfile

from pathlib import Path

from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, File, HTTPException
from fastapi import UploadFile

from sqlalchemy import text, select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

import pandas as pd

from ..model.database import get_db
from ..model.product import Product
from ..model.product_table import ProductTable
from ..model.product_table_ver import ProductTableVersion
from ..model.parameter_schema import ParameterSchema
from ..schema.product_table import (
    ProductTableCreate,
    ProductTableResponse,
    ProductTableUpdate,
    ProductTableVersionResponse,
)
from ..utils.router_utils import to_sql_name_lat
from .parameter_values import mark_datamart_dirty

import io

router = APIRouter(prefix="/tables", tags=["Tables"])

VERSIONS_DIRECTORY = Path("./static/product_table_versions")
MAX_VERSIONS = 5


def normalize_column_name(value):
    return str(value).replace("\xa0", " ").strip()


def normalize_excel_value(value):
    if value is None or pd.isna(value):
        return None

    normalized = " ".join(str(value).split())
    return normalized or None


def validate_sql_identifier(identifier: str) -> None:
    if not identifier.replace("_", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail="Некорректное физическое имя таблицы",
        )


async def read_excel(upload: UploadFile) -> tuple[pd.DataFrame, bytes]:
    contents = await upload.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Загружен пустой файл",
        )

    try:
        df = pd.read_excel(
            io.BytesIO(contents),
            engine="openpyxl",
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Не удалось прочитать Excel: {error}",
        )

    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    df = df.where(pd.notnull(df), None)

    return df, contents


# === Table Schema Endpoints ===


@router.post(
    "",
    response_model=ProductTableResponse,
    status_code=201,
    description="Создание табличной сущности продукта.",
)
async def create_product_table(
        schema: ProductTableCreate,
        db: AsyncSession = Depends(get_db),
):
    product_result = await db.execute(
        select(Product.id).where(
            Product.id == schema.product_id
        )
    )

    if product_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Продукция не найдена",
        )

    clean_name = normalize_column_name(schema.name)

    if not clean_name:
        raise HTTPException(
            status_code=400,
            detail="Название сущности не может быть пустым",
        )

    existing_result = await db.execute(
        select(ProductTable.id).where(
            ProductTable.product_id == schema.product_id,
            ProductTable.name == clean_name,
        )
    )

    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Сущность с таким названием уже существует",
        )

    try:
        entity = ProductTable(
            product_id=schema.product_id,
            name=clean_name,
            physical_table_name=None,
        )

        db.add(entity)

        # Получаем ID новой сущности
        await db.flush()

        entity.physical_table_name = (
            f"product_{schema.product_id}_table_{entity.id}"
        )

        await db.commit()
        await db.refresh(entity)

        return entity

    except Exception as error:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка создания табличной сущности: {error}",
        )


@router.get(
    "",
    description="Получение табличных сущностей продукта.",
)
async def get_product_tables(
        product_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            ProductTable.id,
            ProductTable.product_id,
            ProductTable.name,
            ProductTable.physical_table_name,
            ProductTable.created_at,
            func.count(ProductTableVersion.id).label("versions_count"),
            func.max(ProductTableVersion.version_number).label(
                "current_version"
            ),
        )
        .outerjoin(
            ProductTableVersion,
            ProductTableVersion.product_table_id == ProductTable.id,
        )
        .where(ProductTable.product_id == product_id)
        .group_by(ProductTable.id)
        .order_by(ProductTable.id)
    )

    return [dict(row) for row in result.mappings().all()]


@router.put(
    "/{product_table_id}",
    response_model=ProductTableResponse,
    description="Переименование табличной сущности продукта."
)
async def update_product_table(
        product_table_id: int,
        schema: ProductTableUpdate,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductTable).where(
            ProductTable.id == product_table_id
        )
    )

    entity = result.scalar_one_or_none()

    if entity is None:
        raise HTTPException(
            status_code=404,
            detail="Табличная сущность не найдена",
        )

    clean_name = normalize_column_name(schema.name)

    duplicate_result = await db.execute(
        select(ProductTable.id).where(
            ProductTable.product_id == entity.product_id,
            ProductTable.name == clean_name,
            ProductTable.id != entity.id,
        )
    )

    if duplicate_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Сущность с таким названием уже существует",
        )

    entity.name = clean_name

    await db.commit()
    await db.refresh(entity)

    return entity


@router.post(
    "/{product_table_id}/versions",
    response_model=ProductTableVersionResponse,
    status_code=201,
    description="Загрузка новой версии Excel.",
)
async def upload_product_table_version(
        product_table_id: int,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
):
    entity_result = await db.execute(
        select(ProductTable).where(
            ProductTable.id == product_table_id
        )
    )

    entity = entity_result.scalar_one_or_none()

    if entity is None:
        raise HTTPException(
            status_code=404,
            detail="Табличная сущность не найдена",
        )

    table_name = entity.physical_table_name

    if not table_name:
        raise HTTPException(
            status_code=500,
            detail="У сущности отсутствует физическое имя таблицы",
        )

    validate_sql_identifier(table_name)

    df, contents = await read_excel(file)

    excel_columns = [
        column
        for column in df.columns
        if column.lower() != "id"
    ]

    if not excel_columns:
        raise HTTPException(
            status_code=400,
            detail="В Excel отсутствуют пользовательские колонки",
        )

    excel_map = {
        to_sql_name_lat(column): column
        for column in excel_columns
    }

    sql_columns = list(excel_map.keys())

    # Защита от одинаковой транслитерации
    if len(sql_columns) != len(set(sql_columns)):
        raise HTTPException(
            status_code=400,
            detail=(
                "После преобразования названий несколько колонок "
                "получили одинаковое SQL-имя"
            ),
        )

    version_result = await db.execute(
        select(
            func.coalesce(
                func.max(ProductTableVersion.version_number),
                0,
            )
        ).where(
            ProductTableVersion.product_table_id == entity.id
        )
    )

    next_version = version_result.scalar_one() + 1

    version_directory = (
            VERSIONS_DIRECTORY
            / str(entity.product_id)
            / str(entity.id)
    )
    version_directory.mkdir(parents=True, exist_ok=True)

    safe_extension = (
            os.path.splitext(file.filename or "")[1].lower() or ".xlsx"
    )

    stored_filename = f"version_{next_version}{safe_extension}"
    file_path = version_directory / stored_filename

    files_to_delete: list[str] = []

    try:
        # 1. Сохраняем исходный файл
        with open(file_path, "wb") as destination:
            destination.write(contents)

        # 2. Пересоздаём физическую таблицу актуальной версии
        await db.execute(
            text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
        )

        columns_sql = ", ".join(
            f'"{column}" TEXT'
            for column in sql_columns
        )

        await db.execute(
            text(f"""
                CREATE TABLE "{table_name}" (
                    id SERIAL PRIMARY KEY,
                    {columns_sql}
                )
            """)
        )

        # 3. Заполняем таблицу
        rows = [
            {
                sql_column: normalize_excel_value(
                    record[excel_map[sql_column]]
                )
                for sql_column in sql_columns
            }
            for record in df.to_dict(orient="records")
        ]

        if rows:
            insert_columns = ", ".join(
                f'"{column}"'
                for column in sql_columns
            )
            placeholders = ", ".join(
                f":{column}"
                for column in sql_columns
            )

            await db.execute(
                text(f"""
                    INSERT INTO "{table_name}" ({insert_columns})
                    VALUES ({placeholders})
                """),
                rows,
            )

        # 4. Пересоздаём параметры только этой сущности
        await db.execute(
            delete(ParameterSchema).where(
                ParameterSchema.product_table_id == entity.id
            )
        )

        for position, sql_column in enumerate(sql_columns, start=1):
            db.add(
                ParameterSchema(
                    name=excel_map[sql_column],
                    transliterated_name=sql_column,
                    type="Table",
                    table_name=table_name,
                    product_id=entity.product_id,
                    product_table_id=entity.id,
                    sort=float(position),
                )
            )

        # 5. Старая версия перестаёт быть текущей
        await db.execute(
            update(ProductTableVersion)
            .where(
                ProductTableVersion.product_table_id == entity.id
            )
            .values(is_current=False)
        )

        # 6. Создаём новую версию
        version = ProductTableVersion(
            product_table_id=entity.id,
            version_number=next_version,
            original_filename=file.filename or stored_filename,
            file_path=str(file_path),
            is_current=True,
        )

        db.add(version)
        await db.flush()

        # 7. Оставляем только пять последних версий
        versions_result = await db.execute(
            select(ProductTableVersion)
            .where(
                ProductTableVersion.product_table_id == entity.id
            )
            .order_by(
                ProductTableVersion.version_number.desc(),
                ProductTableVersion.id.desc(),
            )
        )

        versions = list(versions_result.scalars().all())
        old_versions = versions[MAX_VERSIONS:]

        for old_version in old_versions:
            if old_version.file_path:
                files_to_delete.append(old_version.file_path)

            await db.delete(old_version)

        # 8. Помечаем datamart устаревшим
        await mark_datamart_dirty(
            db=db,
            product_id=entity.product_id,
        )

        await db.commit()
        await db.refresh(version)

    except HTTPException:
        await db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise

    except Exception as error:
        await db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки версии: {error}",
        )

    # Старые файлы удаляем после успешного commit
    for old_file_path in files_to_delete:
        try:
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        except OSError:
            pass

    return version


@router.get(
    "/{product_table_id}/versions",
    response_model=list[ProductTableVersionResponse],
    description="История версий сущности."
)
async def get_product_table_versions(
        product_table_id: int,
        db: AsyncSession = Depends(get_db),
):
    entity_result = await db.execute(
        select(ProductTable.id).where(
            ProductTable.id == product_table_id
        )
    )

    if entity_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Табличная сущность не найдена",
        )

    result = await db.execute(
        select(ProductTableVersion)
        .where(
            ProductTableVersion.product_table_id == product_table_id
        )
        .order_by(
            ProductTableVersion.version_number.desc()
        )
    )

    return list(result.scalars().all())


@router.get(
    "/{product_table_id}/versions/{version_id}/download",
    description="Скачивание выбранной версии."
)
async def download_product_table_version(
        product_table_id: int,
        version_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductTableVersion).where(
            ProductTableVersion.id == version_id,
            ProductTableVersion.product_table_id == product_table_id,
        )
    )

    version = result.scalar_one_or_none()

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Версия не найдена",
        )

    if not os.path.exists(version.file_path):
        raise HTTPException(
            status_code=404,
            detail="Файл версии отсутствует на сервере",
        )

    return FileResponse(
        path=version.file_path,
        filename=version.original_filename,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition"
        },
    )


@router.delete(
    "/{product_table_id}",
    description="Удаление табличной сущности со всеми версиями.",
)
async def delete_product_table(
        product_table_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductTable).where(
            ProductTable.id == product_table_id
        )
    )

    entity = result.scalar_one_or_none()

    if entity is None:
        raise HTTPException(
            status_code=404,
            detail="Табличная сущность не найдена",
        )

    table_name = entity.physical_table_name
    product_id = entity.product_id

    versions_result = await db.execute(
        select(ProductTableVersion.file_path).where(
            ProductTableVersion.product_table_id == entity.id
        )
    )

    files_to_delete = [
        path
        for path in versions_result.scalars().all()
        if path
    ]

    try:
        if table_name:
            validate_sql_identifier(table_name)

            await db.execute(
                text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            )

        await db.delete(entity)

        await mark_datamart_dirty(
            db=db,
            product_id=product_id,
        )

        await db.commit()

    except Exception as error:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка удаления сущности: {error}",
        )

    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

    return {
        "id": product_table_id,
        "name": entity.name,
        "message": "Табличная сущность удалена",
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
            SELECT
                physical_table_name,
                name
            FROM product_tables
            WHERE product_id = :product_id
            ORDER BY id
        """),
        {"product_id": product_id},
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
