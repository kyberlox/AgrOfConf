# app/products/router/parameters.py

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile
from sqlalchemy import text

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..model.database import get_db
from ..model.product import Product
from ..model.parameter_schema import ParameterSchema
from ..model.parameter_file import ParameterFile
from ..schema.parameter_schema import ParameterSchemaCreate, ParameterSchemaResponse, ParameterSchemaUpdate
from ..utils.db_utils import create_or_alter_table
from ..utils.router_utils import to_sql_name_lat

router = APIRouter(prefix="/parameters", tags=["Parameters"])

PARAM_FILES_DIR = "./static/parameter_files"
os.makedirs(PARAM_FILES_DIR, exist_ok=True)


# === Parameter Schema Endpoints ===

@router.post("/", response_model=ParameterSchemaResponse, status_code=201)
async def create_parameter_schema(
        schema: ParameterSchemaCreate,
        db: AsyncSession = Depends(get_db)
):
    # Проверка типа
    if schema.type not in ["Table", "Formula", "Drawing"]:
        raise HTTPException(status_code=400, detail="Type must be 'Table', 'Formula' or 'Drawing'")

    # Проверка связи с продуктом
    product_result = await db.execute(
        select(Product).where(Product.id == schema.product_id)
    )
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Invalid product_id")

    # Транслитерируем имя параметра
    translit_name = to_sql_name_lat(schema.name)

    db_schema = ParameterSchema(
        **schema.dict(),
        transliterated_name=to_sql_name_lat(schema.name)
    )

    db.add(db_schema)

    await db.flush()

    if db_schema.sort is None:
        db_schema.sort = float(db_schema.id)

    # Если тип Table — создаём или изменяем таблицу
    if schema.type == "Table":
        if not schema.table_name:
            raise HTTPException(status_code=400, detail="table_name is required")

        await create_or_alter_table(
            db,
            to_sql_name_lat(schema.table_name) + "_table",
            translit_name
        )

    await db.commit()
    await db.refresh(db_schema)
    return db_schema


@router.get("/by_product/{product_id}", response_model=list[ParameterSchemaResponse],
            description="Выведение информации по параметрам продукта по его {ID}.")
async def get_parameters(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ParameterSchema)
        .where(ParameterSchema.product_id == product_id)
        .order_by(ParameterSchema.sort)
    )
    params = result.scalars().all()
    # Для продукта без параметров возвращаем пустой список, а не 404,
    # чтобы фронтенд корректно показывал плашку «Параметры ещё не заданы».
    return list(params)


@router.get("/{param_id}", response_model=ParameterSchemaResponse,
            description="Выведение информации по параметру по его {ID}.")
async def get_parameter(param_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ParameterSchema).where(ParameterSchema.id == param_id))
    param = result.scalar_one_or_none()
    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")
    return param


@router.put("/{param_id}", response_model=ParameterSchemaResponse,
            description="Запрос на изменение полей параметра.")
async def update_parameter(
        param_id: int,
        schema_update: ParameterSchemaUpdate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ParameterSchema).where(ParameterSchema.id == param_id))
    param = result.scalar_one_or_none()

    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")

    update_data = schema_update.dict(exclude_unset=True)

    if "name" in update_data:
        old_translit = param.transliterated_name
        new_translit = to_sql_name_lat(update_data["name"])

        param.name = update_data["name"]
        param.transliterated_name = new_translit

        # если это Table → переименовываем колонку
        if param.type == "Table" and param.table_name and new_translit != old_translit:
            table_name = to_sql_name_lat(param.table_name)# + "_table"

            await db.execute(
                text(f'ALTER TABLE {table_name} RENAME COLUMN "{old_translit}" TO "{new_translit}"')
            )

    for key, value in update_data.items():
        if key != "name":
            setattr(param, key, value)

    await db.commit()
    await db.refresh(param)

    return param

@router.put("/sort/{product_id}", description="Для сортировки параметров со стороны фронтенда")
async def new_sort(product_id: int, data = Body(), db: AsyncSession = Depends(get_db)):

    if data != []:
        for param in data:
            param_id = param["id"]
            new_sort = param["sort"]

            await db.execute(
                text(f'UPDATE public.parameter_schemas SET sort = {new_sort} WHERE id = {param_id};')
            )

        await db.commit()

        result = await db.execute(
            select(ParameterSchema)
            .where(ParameterSchema.product_id == product_id)
            .order_by(ParameterSchema.sort)
        )
        params = result.scalars().all()

        return params

    else:
        raise HTTPException(status_code=404, detail="Parameters not found")

@router.delete("/{param_id}", response_model=ParameterSchemaResponse,
               description="Запрос на удаление полей параметра.")
async def delete_parameter(
        param_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterSchema).where(ParameterSchema.id == param_id)
    )
    param = result.scalar_one_or_none()

    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")

    # Если это параметр типа «Файл» — удаляем его файлы (БД и с диска),
    # иначе внешний ключ не даст удалить сам параметр.
    files_res = await db.execute(
        select(ParameterFile).where(ParameterFile.parameter_id == param_id)
    )
    for pf in files_res.scalars().all():
        if pf.file_path and os.path.exists(pf.file_path):
            os.remove(pf.file_path)
        await db.delete(pf)

    await db.delete(param)
    await db.commit()

    return param


# === Файлы параметра типа «Файл» (Drawing) ===

@router.post("/{param_id}/files", status_code=201,
             description="Загрузка файлов в параметр типа «Файл». Файлы — значения этого параметра.")
async def upload_parameter_files(
        param_id: int,
        files: list[UploadFile] = File(...),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ParameterSchema).where(ParameterSchema.id == param_id))
    param = result.scalar_one_or_none()
    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")

    created = []
    for image in files:
        original = Path(image.filename or "file").name
        file_type = Path(original).suffix
        # Уникализируем имя на диске, но сохраняем оригинальное в БД (для функции).
        disk_name = f"{param_id}_{original}"
        file_path = os.path.join(PARAM_FILES_DIR, disk_name)
        with open(file_path, "wb") as f:
            f.write(await image.read())

        file_url = f"/api/files/parameter_files/{disk_name}"

        record = ParameterFile(
            parameter_id=param_id,
            product_id=param.product_id,
            name=original,
            file_path=file_path,
            file_url=file_url,
        )
        db.add(record)
        created.append({
            "name": original,
            "file_path": file_path,
            "file_url": file_url,
        })

    await db.commit()

    return created


@router.get("/{param_id}/files", description="Список файлов параметра типа «Файл».")
async def get_parameter_files(param_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ParameterFile)
        .where(ParameterFile.parameter_id == param_id)
        .order_by(ParameterFile.id)
    )
    return result.scalars().all()


@router.delete("/{param_id}/files/{file_id}", status_code=204,
               description="Удаление файла параметра.")
async def delete_parameter_file(
        param_id: int,
        file_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterFile).where(
            ParameterFile.id == file_id,
            ParameterFile.parameter_id == param_id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="File not found")

    if node.file_path and os.path.exists(node.file_path):
        os.remove(node.file_path)

    await db.delete(node)
    await db.commit()

    return None
