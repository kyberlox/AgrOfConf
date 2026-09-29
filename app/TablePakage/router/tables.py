# app/products/router/tables.py
import os
import re
import tempfile

from pathlib import Path

from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, File, HTTPException
from fastapi import UploadFile

from sqlalchemy import text, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

import pandas as pd

from ..model.database import get_db
from ..model.product import Product
from ..model.product_table import ProductTable
from ..model.product_table_ver import ProductTableVersion
from ..model.parameter_schema import ParameterSchema
from ..model.parameter_file import ParameterFile
from ..schema.product_table import (
    ProductTableCreate,
    ProductTableResponse,
    ProductTableUpdate,
    ProductTableVersionResponse,
)
from ..utils.router_utils import to_sql_name_lat
from .parameter_values import mark_datamart_dirty
from app.TableSearch.utils.dm_search import rebuild_dm

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


def is_price_column(column_name: str) -> bool:
    """Ценовые колонки определяются по слову «цена» в названии."""
    return "цена" in str(column_name).lower()


def format_price_value(value):
    """Приводит цену к виду 123456.78 — ровно два знака после запятой, без округления.

    - 432123       -> 432123.00
    - 234234.123123-> 234234.12
    - 234234.5     -> 234234.50
    - 1 234 567,89 -> 1234567.89
    - «текст»      -> как есть
    """
    if value is None:
        return None

    original = str(value).strip()

    match = re.match(r"^([+\-]?\d[\d\s\u00a0.,]*)(.*)$", original)
    if not match:
        return original

    num_text, suffix = match.group(1), match.group(2)
    suffix = suffix.strip()

    sign = ""
    if num_text[:1] in ("+", "-"):
        sign, num_text = num_text[:1], num_text[1:]

    compact = num_text.replace(" ", "").replace("\u00a0", "")

    last_dot = compact.rfind(".")
    last_comma = compact.rfind(",")

    if last_dot == -1 and last_comma == -1:
        integer, decimals = compact, "00"
    else:
        separator = "," if last_comma > last_dot else "."
        separator_index = compact.rfind(separator)
        integer = compact[:separator_index].replace(".", "").replace(",", "") or "0"
        decimals = compact[separator_index + 1:].replace(".", "").replace(",", "")[:2].ljust(2, "0")

    formatted = f"{sign}{integer}.{decimals}"

    return f"{formatted} {suffix}" if suffix else formatted


def validate_sql_identifier(identifier: str) -> None:
    if not identifier.replace("_", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail="Некорректное физическое имя таблицы",
        )


async def _collect_entity_files(
        db: AsyncSession,
        entity: ProductTable,
) -> list[str]:
    """Собирает пути файлов (версий Excel и файлов параметров) сущности
    для удаления с диска после успешного commit."""
    paths: list[str] = []

    versions_result = await db.execute(
        select(ProductTableVersion.file_path).where(
            ProductTableVersion.product_table_id == entity.id
        )
    )
    for path in versions_result.scalars().all():
        if path:
            paths.append(path)

    params_result = await db.execute(
        select(ParameterSchema.id).where(
            ParameterSchema.product_table_id == entity.id
        )
    )
    param_ids = [row[0] for row in params_result.all()]

    if param_ids:
        files_result = await db.execute(
            select(ParameterFile.file_path).where(
                ParameterFile.parameter_id.in_(param_ids)
            )
        )
        for path in files_result.scalars().all():
            if path:
                paths.append(path)

    return paths


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

    df, contents = await read_excel(file)

    return await _load_excel_version(
        db, entity, df, contents, source_filename=file.filename or ""
    )


async def _load_excel_version(
        db: AsyncSession,
        entity: ProductTable,
        df: pd.DataFrame,
        contents: bytes,
        source_filename: str,
) -> ProductTableVersion:
    table_name = entity.physical_table_name

    if not table_name:
        raise HTTPException(
            status_code=500,
            detail="У сущности отсутствует физическое имя таблицы",
        )

    validate_sql_identifier(table_name)

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
            os.path.splitext(source_filename or "")[1].lower() or ".xlsx"
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
        price_columns = {
            sql_column
            for sql_column in sql_columns
            if is_price_column(excel_map[sql_column])
        }

        def normalize_cell(sql_column: str, record: dict):
            normalized = normalize_excel_value(record[excel_map[sql_column]])

            if sql_column in price_columns:
                return format_price_value(normalized)

            return normalized

        rows = [
            {
                sql_column: normalize_cell(sql_column, record)
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

        # 4. Обновляем параметры (upsert): без дублей и с сохранением связей с блоками.
        existing_result = await db.execute(
            select(ParameterSchema).where(
                ParameterSchema.product_table_id == entity.id
            )
        )
        existing_rows = list(existing_result.scalars().all())

        # Лечим уже накопленные дубли: оставляем один параметр на имя,
        # предпочитая тот, что уже привязан к блоку.
        by_name: dict[str, list[ParameterSchema]] = {}
        for row in existing_rows:
            by_name.setdefault(row.transliterated_name, []).append(row)

        existing_params: dict[str, ParameterSchema] = {}

        for key, rows in by_name.items():
            keeper = next((r for r in rows if r.block_id is not None), rows[0])

            for duplicate in rows:
                if duplicate is not keeper:
                    await db.delete(duplicate)

            existing_params[key] = keeper

        new_param_names = set(sql_columns)

        for position, sql_column in enumerate(sql_columns, start=1):
            current = existing_params.get(sql_column)

            if current is not None:
                current.name = excel_map[sql_column]
                current.table_name = table_name
                current.sort = float(position)
                continue

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

        # Параметры, ушедшие из файла, удаляем; у оставшихся блоки не трогаем.
        for old_key, old_row in existing_params.items():
            if old_key not in new_param_names:
                await db.delete(old_row)

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
            original_filename=source_filename or stored_filename,
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

        # 9. Обновляем витрину (кэш значений) сразу.
        # Если пересборка упадёт — is_dirty уже True (шаг 8),
        # и витрина пересоберётся при первом же обращении к поиску.
        try:
            await rebuild_dm(db=db, product_id=entity.product_id)
        except Exception as error:
            print(f"[tables.upload] Ошибка пересборки витрины: {error}")

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


@router.post(
    "/upload_xlsx",
    status_code=201,
    description=(
        "Загрузка Excel с созданием таблицы и параметров продукта. "
        "Если таблица с таким именем уже существует — перезагружает её версию. "
        "Если в продукте уже есть таблица с похожим набором колонок (например, "
        "«Версия3» и «Версия4» одного прайса, отличающиеся лишь парой колонок) — "
        "она обновляется, а лишние таблицы с похожим набором колонок удаляются, "
        "чтобы параметры не дублировались."
    ),
)
async def upload_xlsx(
        product_id: int,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
):
    """Создаёт/обновляет таблицу продукта из Excel и соответствующие параметры."""
    product_result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    if product_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Продукт не найден")

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

    file_sql_columns = {
        to_sql_name_lat(column)
        for column in excel_columns
    }

    if len(file_sql_columns) != len(set(file_sql_columns)):
        raise HTTPException(
            status_code=400,
            detail=(
                "После преобразования названий несколько колонок "
                "получили одинаковое SQL-имя"
            ),
        )

    base_name = os.path.splitext(file.filename or "table")[0]
    physical = f"{to_sql_name_lat(base_name)}_p{product_id}"
    validate_sql_identifier(physical)

    # Все сущности продукта и их «табличные» параметры (для сравнения колонок).
    result = await db.execute(
        select(ProductTable).where(
            ProductTable.product_id == product_id
        ).order_by(ProductTable.id)
    )
    entities = list(result.scalars().all())

    columns_result = await db.execute(
        select(
            ParameterSchema.product_table_id,
            ParameterSchema.transliterated_name,
            ParameterSchema.block_id,
        ).where(
            ParameterSchema.product_id == product_id,
            ParameterSchema.type == "Table",
        )
    )
    entity_columns: dict[int, set] = {}
    entity_block_linked: dict[int, bool] = {}

    for row in columns_result.mappings().all():
        entity_id = row["product_table_id"]
        if entity_id is None:
            continue
        entity_columns.setdefault(entity_id, set()).add(row["transliterated_name"])
        if row["block_id"] is not None:
            entity_block_linked[entity_id] = True

    def column_similarity(entity: ProductTable) -> float:
        params = entity_columns.get(entity.id)
        if params is None or not params or not file_sql_columns:
            return 0.0
        intersect = len(params & file_sql_columns)
        return intersect / max(len(params), len(file_sql_columns))

    by_physical = next(
        (e for e in entities if e.physical_table_name == physical),
        None,
    )
    by_name = next(
        (e for e in entities if e.name == base_name),
        None,
    )
    SIMILARITY_THRESHOLD = 0.75
    similar_entities = [
        e for e in entities
        if column_similarity(e) >= SIMILARITY_THRESHOLD
    ]

    # Целевая сущность: 1) то же физическое имя (тот же файл), 2) то же имя,
    # 3) похожий набор колонок (предпочитаем ту, что уже связана с блоками,
    # затем более похожую, затем старейшую).
    target = by_physical or by_name
    if target is None and similar_entities:
        similar_entities.sort(
            key=lambda e: (
                not entity_block_linked.get(e.id),
                -column_similarity(e),
                e.id,
            )
        )
        target = similar_entities[0]

    redundant_entities = [
        e for e in similar_entities
        if target is not None and e is not target
    ]

    files_to_delete: list[str] = []

    if target is not None:
        # Переносим связи параметров с блоками с удаляемых сущностей на живую.
        for redundant in redundant_entities:
            redundant_params = await db.execute(
                select(ParameterSchema).where(
                    ParameterSchema.product_table_id == redundant.id
                )
            )
            for param in redundant_params.scalars().all():
                if param.block_id is None:
                    continue
                survivor_result = await db.execute(
                    select(ParameterSchema.id).where(
                        ParameterSchema.product_table_id == target.id,
                        ParameterSchema.transliterated_name == param.transliterated_name,
                    )
                )
                survivor_id = survivor_result.scalar_one_or_none()
                if survivor_id is not None:
                    await db.execute(
                        update(ParameterSchema)
                        .where(ParameterSchema.id == survivor_id)
                        .values(block_id=param.block_id)
                    )

        # Переименовываем под новое имя файла, если оно никем не занято.
        if base_name != target.name:
            name_taken = await db.execute(
                select(ProductTable.id).where(
                    ProductTable.product_id == product_id,
                    ProductTable.name == base_name,
                    ProductTable.id != target.id,
                )
            )
            if name_taken.scalar_one_or_none() is None:
                target.name = base_name
    else:
        target = ProductTable(
            name=base_name,
            product_id=product_id,
            physical_table_name=physical,
        )
        db.add(target)
        await db.flush()

    # Удаляем лишние сущности с идентичным набором колонок (сжатие дублей).
    for redundant in redundant_entities:
        files_to_delete.extend(
            await _collect_entity_files(db, redundant)
        )

        if redundant.physical_table_name:
            validate_sql_identifier(redundant.physical_table_name)
            await db.execute(
                text(f'DROP TABLE IF EXISTS "{redundant.physical_table_name}" CASCADE')
            )

        # Каскадом удаляются версии сущности, её параметры и файлы параметров.
        await db.delete(redundant)

    # Переиспользуем общую логику загрузки версии (создание таблицы + параметров).
    await _load_excel_version(
        db, target, df, contents, source_filename=file.filename or ""
    )

    # Старые файлы удалённых сущностей чистим после успешного commit.
    for old_file_path in files_to_delete:
        try:
            if old_file_path and os.path.exists(old_file_path):
                os.remove(old_file_path)
        except OSError:
            pass

    return {"status": "ok"}


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

    # Физические файлы для удаления с диска после успешного commit
    files_to_delete: list[str] = []

    # Параметры этой сущности
    params_result = await db.execute(
        select(ParameterSchema).where(
            ParameterSchema.product_table_id == entity.id
        )
    )
    params = list(params_result.scalars().all())

    # Файлы параметров типа «Файл», привязанные к параметрам этой сущности,
    # удаляем до удаления самих параметров (иначе внешний ключ помешает)
    if params:
        param_ids = [p.id for p in params]
        pf_result = await db.execute(
            select(ParameterFile).where(
                ParameterFile.parameter_id.in_(param_ids)
            )
        )
        for pf in pf_result.scalars().all():
            if pf.file_path and os.path.exists(pf.file_path):
                files_to_delete.append(pf.file_path)
            await db.delete(pf)

    # Файлы версий (файлы Excel) — для удаления с диска после commit
    versions_result = await db.execute(
        select(ProductTableVersion.file_path).where(
            ProductTableVersion.product_table_id == entity.id
        )
    )

    for path in versions_result.scalars().all():
        if path and os.path.exists(path):
            files_to_delete.append(path)

    try:
        if table_name:
            validate_sql_identifier(table_name)

            await db.execute(
                text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            )

        # Удаляем параметры сущности явно (вместе с их файлами)
        for p in params:
            await db.delete(p)

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


@router.delete(
    "/{product_id}/{table_name}",
    description="Удаление табличной сущности продукта по физическому имени таблицы.",
)
async def delete_product_table_by_name(
        product_id: int,
        table_name: str,
        db: AsyncSession = Depends(get_db),
):
    """Удаляет табличную сущность продукта по физическому имени таблицы.

    Используется фронтендом (DELETE /api/tables/{product_id}/{table_name}).
    Покрывает как таблицы, зарегистрированные в `product_tables`, так и
    «легаси»-параметры с физической таблицей без записи в реестре.
    """
    result = await db.execute(
        select(ProductTable).where(
            ProductTable.product_id == product_id,
            ProductTable.physical_table_name == table_name,
        )
    )
    entity = result.scalar_one_or_none()

    if entity is not None:
        return await delete_product_table(entity.id, db)

    # Легаси-таблица: параметры с физическим именем без записи в product_tables
    params_result = await db.execute(
        select(ParameterSchema).where(
            ParameterSchema.product_id == product_id,
            ParameterSchema.table_name == table_name,
        )
    )
    params = list(params_result.scalars().all())

    if not params:
        raise HTTPException(
            status_code=404,
            detail="Табличная сущность не найдена",
        )

    # Физические файлы зависимых сущностей для удаления с диска после commit
    files_to_delete: list[str] = []

    # Файлы параметров типа «Файл» (иностранный ключ не даст удалить параметры)
    param_ids = [p.id for p in params]
    pf_result = await db.execute(
        select(ParameterFile).where(
            ParameterFile.parameter_id.in_(param_ids)
        )
    )
    for pf in pf_result.scalars().all():
        if pf.file_path and os.path.exists(pf.file_path):
            files_to_delete.append(pf.file_path)
        await db.delete(pf)

    try:
        for p in params:
            await db.delete(p)

        if table_name:
            validate_sql_identifier(table_name)
            await db.execute(
                text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            )

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
        "id": None,
        "name": table_name,
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
