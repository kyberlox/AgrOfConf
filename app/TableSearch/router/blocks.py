"""
Роутер для блоков параметров продукта.

Блоки больше НЕ хардкодятся (как раньше в словаре `splitting`), а хранятся в БД:
- таблица `parameter_blocks` — сами блоки (product_id, name, sort);
- поле `parameter_schemas.block_id` — привязка параметра к блоку.

Эндпоинт `GET /blocks/by_product/{id}` сохраняет прежний формат ответа
`{ "Название блока": ["имя параметра", ...] }`, чтобы конфигуратор продолжал
работать без изменений.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from typing import Optional, List

from app.TablePakage.model.database import get_db
from app.TablePakage.model.parameter_block import ParameterBlock
from app.TablePakage.model.parameter_schema import ParameterSchema
from app.TablePakage.model.product import Product
from app.TablePakage.utils.router_utils import to_sql_name_lat
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/blocks", tags=["Blocks"])

# Набор параметров блока «Контактные данные» (по образцу старого движка agent_contacts).
CONTACT_PARAM_NAMES = [
    "ФИО Заказчика",
    "Телефон Заказчика",
    "Email Заказчика",
    "Организация Заказчика",
    "Должность Заказчика",
    "Проектная организация",
    "Примечание",
    "Адрес Заказчика",
]
CONTACT_BLOCK_NAME = "👤 Контактные данные"


class BlockCreate(BaseModel):
    product_id: int
    name: str


class BlockUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort: Optional[float] = None
    properties: Optional[dict] = None


class BlockReorderItem(BaseModel):
    id: int
    sort: float


class BlockReorder(BaseModel):
    items: List[BlockReorderItem]


class BlockAssign(BaseModel):
    parameter_ids: List[int]


def _param_to_ref(p: ParameterSchema) -> dict:
    return {"id": p.id, "name": p.name, "type": p.type, "required_type": p.required_type}


def _apply_props_to_params(params, props: Optional[dict]) -> None:
    """Применяет свойства блока к его параметрам."""
    if not props:
        return
    for p in params:
        if "editable" in props:
            p.editable = bool(props["editable"])
        if "visibility" in props:
            p.visibility = bool(props["visibility"])


@router.get("/by_product/{product_id}")
async def get_by_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Возвращает блоки продукта с их параметрами и режимом отображения.

    Формат:
      [{"name": "...", "display": "group|sequential", "params": ["имя", ...]}, ...]
    """
    blocks_result = await db.execute(
        select(ParameterBlock)
        .where(ParameterBlock.product_id == product_id)
        .order_by(ParameterBlock.sort)
    )
    blocks = blocks_result.scalars().all()

    result = []
    for block in blocks:
        params_result = await db.execute(
            select(ParameterSchema)
            .where(ParameterSchema.block_id == block.id)
            .order_by(ParameterSchema.sort)
        )
        names = [p.name for p in params_result.scalars().all()]
        display = (block.properties or {}).get("display", "group")
        result.append({"name": block.name, "display": display, "params": names})

    return result


@router.get("/manage/{product_id}")
async def get_manage(product_id: int, db: AsyncSession = Depends(get_db)):
    """Возвращает структуру блоков для админки (drag-and-drop).

    Формат:
      { "blocks": [{"id","name","params":[{"id","name"}]}], "unassigned": [{"id","name"}] }
    """
    blocks_result = await db.execute(
        select(ParameterBlock)
        .where(ParameterBlock.product_id == product_id)
        .order_by(ParameterBlock.sort)
    )
    blocks = blocks_result.scalars().all()

    payload_blocks = []
    for block in blocks:
        params_result = await db.execute(
            select(ParameterSchema)
            .where(ParameterSchema.block_id == block.id)
            .order_by(ParameterSchema.sort)
        )
        payload_blocks.append({
            "id": block.id,
            "name": block.name,
            "description": block.description,
            "sort": block.sort,
            "properties": block.properties or {},
            "params": [_param_to_ref(p) for p in params_result.scalars().all()],
        })

    unassigned_result = await db.execute(
        select(ParameterSchema)
        .where(ParameterSchema.product_id == product_id, ParameterSchema.block_id.is_(None))
        .order_by(ParameterSchema.sort)
    )
    unassigned = [_param_to_ref(p) for p in unassigned_result.scalars().all()]

    return {"blocks": payload_blocks, "unassigned": unassigned}


@router.post("/", status_code=201)
async def create_block(body: BlockCreate, db: AsyncSession = Depends(get_db)):
    """Создаёт новый блок параметров продукта."""
    product = await db.get(Product, body.product_id)
    if not product:
        raise HTTPException(status_code=400, detail="Invalid product_id")

    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Block name is required")

    exists = await db.execute(
        select(ParameterBlock).where(
            ParameterBlock.product_id == body.product_id,
            ParameterBlock.name == name,
        )
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Block with this name already exists")

    max_sort = await db.execute(
        select(func.max(ParameterBlock.sort)).where(ParameterBlock.product_id == body.product_id)
    )
    next_sort = (max_sort.scalar() or 0) + 1

    block = ParameterBlock(product_id=body.product_id, name=name, sort=next_sort)
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return {"id": block.id, "name": block.name, "sort": block.sort}


@router.put("/{block_id}")
async def update_block(block_id: int, body: BlockUpdate, db: AsyncSession = Depends(get_db)):
    """Переименовывает блок или меняет его сортировку."""
    block = await db.get(ParameterBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    if body.name is not None and body.name.strip():
        dup = await db.execute(
            select(ParameterBlock).where(
                ParameterBlock.product_id == block.product_id,
                ParameterBlock.name == body.name.strip(),
                ParameterBlock.id != block_id,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Block with this name already exists")
        block.name = body.name.strip()

    if body.sort is not None:
        block.sort = body.sort

    if body.description is not None:
        block.description = body.description

    # Свойства блока применяются ко всем его параметрам.
    if body.properties is not None:
        block.properties = body.properties
        params_result = await db.execute(
            select(ParameterSchema).where(ParameterSchema.block_id == block_id)
        )
        _apply_props_to_params(params_result.scalars().all(), body.properties)

    await db.commit()
    await db.refresh(block)
    return {"id": block.id, "name": block.name, "sort": block.sort, "properties": block.properties or {}}


@router.delete("/{block_id}")
async def delete_block(block_id: int, db: AsyncSession = Depends(get_db)):
    """Удаляет блок и освобождает его параметры (block_id → NULL)."""
    block = await db.get(ParameterBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    params_result = await db.execute(
        select(ParameterSchema).where(ParameterSchema.block_id == block_id)
    )
    for p in params_result.scalars().all():
        p.block_id = None

    await db.delete(block)
    await db.commit()
    return {"ok": True}


@router.post("/reorder")
async def reorder_blocks(body: BlockReorder, db: AsyncSession = Depends(get_db)):
    """Изменяет порядок блоков."""
    for item in body.items:
        block = await db.get(ParameterBlock, item.id)
        if block:
            block.sort = item.sort
    await db.commit()
    return {"ok": True}


@router.post("/{block_id}/assign")
async def assign_parameters(block_id: int, body: BlockAssign, db: AsyncSession = Depends(get_db)):
    """Привязывает указанные параметры к блоку."""
    block = await db.get(ParameterBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    if not body.parameter_ids:
        return {"ok": True, "assigned": []}

    params_result = await db.execute(
        select(ParameterSchema).where(ParameterSchema.id.in_(body.parameter_ids))
    )
    params = params_result.scalars().all()
    # Только параметры того же продукта, что и блок.
    block_params = [p for p in params if p.product_id == block.product_id]
    for p in block_params:
        p.block_id = block.id
    # Наследуем свойства блока новым параметрам.
    _apply_props_to_params(block_params, block.properties or {})

    await db.commit()
    return {"ok": True, "assigned": [p.id for p in block_params]}


@router.post("/unassign")
async def unassign_parameters(body: BlockAssign, db: AsyncSession = Depends(get_db)):
    """Возвращает параметры в пул «не распределённых» (block_id → NULL)."""
    if not body.parameter_ids:
        return {"ok": True, "unassigned": []}

    params_result = await db.execute(
        select(ParameterSchema).where(ParameterSchema.id.in_(body.parameter_ids))
    )
    params = params_result.scalars().all()
    for p in params:
        p.block_id = None

    await db.commit()
    return {"ok": True, "unassigned": [p.id for p in params]}


@router.post("/{product_id}/generate_contacts", status_code=201)
async def generate_contacts(product_id: int, db: AsyncSession = Depends(get_db)):
    """Создаёт блок «Контактные данные» и его параметры (по образцу старого движка).

    Если блок уже есть — добавляются только недостающие параметры.
    """
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=400, detail="Invalid product_id")

    # 1. Находим или создаём блок.
    block_result = await db.execute(
        select(ParameterBlock).where(
            ParameterBlock.product_id == product_id,
            ParameterBlock.name == CONTACT_BLOCK_NAME,
        )
    )
    block = block_result.scalar_one_or_none()
    if not block:
        max_sort = await db.execute(
            select(func.max(ParameterBlock.sort)).where(ParameterBlock.product_id == product_id)
        )
        block = ParameterBlock(
            product_id=product_id,
            name=CONTACT_BLOCK_NAME,
            sort=(max_sort.scalar() or 0) + 1,
        )
        db.add(block)
        await db.flush()

    # 2. Для каждого имени создаём параметр, если его ещё нет у продукта.
    created = []
    for name in CONTACT_PARAM_NAMES:
        exists = await db.execute(
            select(ParameterSchema).where(
                ParameterSchema.product_id == product_id,
                ParameterSchema.name == name,
            )
        )
        if exists.scalar_one_or_none():
            continue

        max_param_sort = await db.execute(
            select(func.max(ParameterSchema.sort)).where(ParameterSchema.product_id == product_id)
        )
        param = ParameterSchema(
            name=name,
            transliterated_name=to_sql_name_lat(name),
            description="Поле блока «Контактные данные»",
            type="Formula",
            required_type="user_input",
            visibility=True,
            product_id=product_id,
            block_id=block.id,
            sort=(max_param_sort.scalar() or 0) + 1,
        )
        db.add(param)
        created.append(name)

    await db.commit()
    return {"block_id": block.id, "block_name": block.name, "created": created}