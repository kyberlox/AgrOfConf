"""
Экспорт/импорт полной конфигурации продукта для переноса между серверами.

Формат — ZIP-архив:
  config.json              — вся конфигурация (продукт, блоки, параметры, свойства, порядок, таблицы, файлы)
  tables/<name>.xlsx       — исходные Excel-файлы таблиц продукта
  files/...                — файлы параметров типа «Файл» (картинки и т.п.)

Импорт переиспользует штатный механизм загрузки таблиц (/upload_xlsx), поэтому
таблицы и их табличные параметры воссоздаются тем же способом, что и при ручном
создании в интерфейсе.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.database import get_db
from ..model.product import Product
from ..model.parameter_schema import ParameterSchema
from ..model.parameter_block import ParameterBlock
from ..model.product_table import ProductTable
from ..model.product_table_ver import ProductTableVersion
from ..model.parameter_file import ParameterFile
from ..utils.router_utils import to_sql_name_lat

from .tables import upload_xlsx

router = APIRouter(prefix="/products", tags=["Product porting"])

PARAM_FILES_DIR = "./static/parameter_files"
os.makedirs(PARAM_FILES_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Экспорт
# ---------------------------------------------------------------------------

async def _latest_version(db: AsyncSession, table: ProductTable):
    res = await db.execute(
        select(ProductTableVersion)
        .where(ProductTableVersion.product_table_id == table.id)
        .order_by(
            ProductTableVersion.version_number.desc(),
            ProductTableVersion.id.desc(),
        )
    )
    return res.scalars().first()


async def _build_config(db: AsyncSession, product_id: int) -> dict:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")

    params = (
        await db.execute(
            select(ParameterSchema)
            .where(ParameterSchema.product_id == product_id)
            .order_by(ParameterSchema.sort)
        )
    ).scalars().all()

    blocks = (
        await db.execute(
            select(ParameterBlock)
            .where(ParameterBlock.product_id == product_id)
            .order_by(ParameterBlock.sort)
        )
    ).scalars().all()

    tables = (
        await db.execute(
            select(ProductTable).where(ProductTable.product_id == product_id)
        )
    ).scalars().all()

    pfiles = (
        await db.execute(
            select(ParameterFile).where(ParameterFile.product_id == product_id)
        )
    ).scalars().all()

    block_id_to_name = {b.id: b.name for b in blocks}
    table_id_to_name = {t.id: t.name for t in tables}
    file_id_to_param = {p.id: p.name for p in params}

    config = {
        "version": 1,
        "product": {
            "name": product.name,
            "description": product.description,
            "manufacturer": product.manufacturer,
        },
        "blocks": [
            {
                "name": b.name,
                "description": b.description,
                "sort": b.sort,
                "properties": b.properties or {},
            }
            for b in blocks
        ],
        "parameters": [
            {
                "name": p.name,
                "transliterated_name": p.transliterated_name,
                "type": p.type,
                "description": p.description,
                "measuring_unit": p.measuring_unit,
                "visibility": p.visibility,
                "editable": p.editable,
                "required_type": p.required_type,
                "field_of_view": p.field_of_view,
                "formula_config": p.formula_config,
                "sort": p.sort,
                "block": block_id_to_name.get(p.block_id),
                # Для табличных параметров — имя таблицы-сущности (без _p{id}).
                "table_ref": table_id_to_name.get(p.product_table_id),
                "table_name": p.table_name,
            }
            for p in params
        ],
        "tables": [
            {"name": t.name, "file": f"tables/{t.name}.xlsx"}
            for t in tables
        ],
        "parameter_files": [],
    }

    # Файлы параметров (картинки/документы).
    by_param: dict[int, list] = {}
    for pf in pfiles:
        by_param.setdefault(pf.parameter_id, []).append(pf)
    for pid, items in by_param.items():
        config["parameter_files"].append({
            "parameter": file_id_to_param.get(pid),
            "files": [
                {"name": f.name, "file": f"files/{f.name}"}
                for f in items
            ],
        })

    return config


def _zip_bytes(config: dict, tables_files: list[tuple], param_files: list[tuple]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("config.json", json.dumps(config, ensure_ascii=False, indent=2))
        for zip_name, data in tables_files + param_files:
            zf.writestr(zip_name, data)
    return buffer.getvalue()


@router.get("/{product_id}/export", description="Экспорт полной конфигурации продукта в ZIP.")
async def export_product(product_id: int, db: AsyncSession = Depends(get_db)):
    config = await _build_config(db, product_id)

    tables_files: list[tuple] = []
    for t in config["tables"]:
        table = (
            await db.execute(
                select(ProductTable).where(
                    ProductTable.product_id == product_id,
                    ProductTable.name == t["name"],
                )
            )
        ).scalar_one_or_none()
        if not table:
            continue
        ver = await _latest_version(db, table)
        if not ver or not ver.file_path or not os.path.exists(ver.file_path):
            continue
        ext = Path(ver.original_filename or t["name"] + ".xlsx").suffix.lower() or ".xlsx"
        zip_name = f"tables/{t['name']}{ext}"
        t["file"] = zip_name
        with open(ver.file_path, "rb") as f:
            tables_files.append((zip_name, f.read()))

    param_files: list[tuple] = []
    for group in config["parameter_files"]:
        for fobj in group["files"]:
            pf = (
                await db.execute(
                    select(ParameterFile).where(
                        ParameterFile.product_id == product_id,
                        ParameterFile.name == fobj["name"],
                    )
                )
            ).scalars().first()
            if pf and pf.file_path and os.path.exists(pf.file_path):
                with open(pf.file_path, "rb") as f:
                    param_files.append((fobj["file"], f.read()))

    data = _zip_bytes(config, tables_files, param_files)
    product = await db.get(Product, product_id)
    safe_name = quote((product.name or "product").replace("/", "_")) + ".zip"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
    )


# ---------------------------------------------------------------------------
# Импорт
# ---------------------------------------------------------------------------

def _make_upload(name: str, data: bytes) -> StarletteUploadFile:
    return StarletteUploadFile(filename=name, file=io.BytesIO(data))


@router.post("/import", status_code=201, description="Создание продукта из ZIP-конфигурации.")
async def import_product(
        archive: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
):
    tmp_dir = tempfile.mkdtemp(prefix="prod_import_")
    try:
        zip_path = os.path.join(tmp_dir, "archive.zip")
        with open(zip_path, "wb") as f:
            f.write(await archive.read())

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        cfg_path = os.path.join(tmp_dir, "config.json")
        if not os.path.exists(cfg_path):
            raise HTTPException(status_code=400, detail="В архиве нет config.json")

        with open(cfg_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        product_data = config.get("product", {})
        product = Product(
            name=product_data.get("name") or "Импортированный продукт",
            description=product_data.get("description"),
            manufacturer=product_data.get("manufacturer"),
        )
        db.add(product)
        await db.flush()
        new_product_id = product.id

        # 1. Таблицы (через штатный механизм -> таблица данных + табличные параметры).
        tables_map: dict[str, ProductTable] = {}
        for tconf in config.get("tables", []):
            rel = tconf.get("file")
            if not rel:
                continue
            file_path = os.path.join(tmp_dir, *rel.split("/"))
            if not os.path.exists(file_path):
                continue
            with open(file_path, "rb") as f:
                data = f.read()
            base_name = tconf.get("name") or os.path.splitext(os.path.basename(rel))[0]
            ext = os.path.splitext(rel)[1].lower() or ".xlsx"
            uf = _make_upload(f"{base_name}{ext}", data)
            await upload_xlsx(product_id=new_product_id, file=uf, db=db)
            await db.refresh(product)

        # Находим созданные таблицы.
        created_tables = (
            await db.execute(
                select(ProductTable).where(ProductTable.product_id == new_product_id)
            )
        ).scalars().all()
        for t in created_tables:
            tables_map[t.name] = t

        # 2. Блоки.
        block_id_by_name: dict[str, int] = {}
        for bconf in config.get("blocks", []):
            block = ParameterBlock(
                product_id=new_product_id,
                name=bconf.get("name"),
                description=bconf.get("description"),
                sort=bconf.get("sort"),
                properties=bconf.get("properties") or {},
            )
            db.add(block)
            await db.flush()
            block_id_by_name[block.name] = block.id

        # 3. Параметры.
        param_id_by_name: dict[str, int] = {}
        for pconf in config.get("parameters", []):
            ptype = pconf.get("type")
            pname = pconf.get("name")
            translit = pconf.get("transliterated_name") or to_sql_name_lat(pname)
            block_id = block_id_by_name.get(pconf.get("block")) if pconf.get("block") else None
            common = {
                "description": pconf.get("description"),
                "measuring_unit": pconf.get("measuring_unit"),
                "visibility": pconf.get("visibility", True),
                "editable": pconf.get("editable", True),
                "required_type": pconf.get("required_type", "list"),
                "field_of_view": pconf.get("field_of_view"),
                "formula_config": pconf.get("formula_config"),
                "sort": pconf.get("sort"),
                "block_id": block_id,
            }

            target = None
            if ptype == "Table":
                table = tables_map.get(pconf.get("table_ref"))
                if table is None:
                    continue
                found = (
                    await db.execute(
                        select(ParameterSchema).where(
                            ParameterSchema.product_table_id == table.id,
                            ParameterSchema.transliterated_name == translit,
                        )
                    )
                ).scalar_one_or_none()
                if found:
                    target = found
                    target.block_id = block_id
                    target.sort = common["sort"]
                else:
                    target = ParameterSchema(
                        name=pname,
                        transliterated_name=translit,
                        type="Table",
                        table_name=table.physical_table_name,
                        product_id=new_product_id,
                        product_table_id=table.id,
                        **common,
                    )
                    db.add(target)
            else:
                target = ParameterSchema(
                    name=pname,
                    transliterated_name=translit,
                    type=ptype,
                    product_id=new_product_id,
                    **common,
                )
                db.add(target)

            await db.flush()
            if target and target.id:
                param_id_by_name[pname] = target.id

        # 4. Файлы параметров (картинки и пр.).
        for group in config.get("parameter_files", []):
            param_name = group.get("parameter")
            pid = param_id_by_name.get(param_name)
            if not pid:
                continue
            for fobj in group.get("files", []):
                rel = fobj.get("file")
                if not rel:
                    continue
                file_path = os.path.join(tmp_dir, *rel.split("/"))
                if not os.path.exists(file_path):
                    continue
                with open(file_path, "rb") as f:
                    data = f.read()
                orig_name = fobj.get("name") or os.path.basename(rel)
                disk_name = f"{pid}_{orig_name}"
                dest = os.path.join(PARAM_FILES_DIR, disk_name)
                with open(dest, "wb") as f:
                    f.write(data)
                db.add(ParameterFile(
                    parameter_id=pid,
                    product_id=new_product_id,
                    name=orig_name,
                    file_path=dest,
                    file_url=f"/api/files/parameter_files/{disk_name}",
                ))

        await db.commit()

        return {
            "id": new_product_id,
            "name": product.name,
            "parameters": len(param_id_by_name),
            "tables": len(tables_map),
        }

    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)