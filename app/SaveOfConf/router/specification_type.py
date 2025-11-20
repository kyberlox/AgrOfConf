from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..model.database import get_db
from ..model.specification_type import SpecificationType as SpecificationTypeModel
from ..schema.specification_type import SpecificationType, SpecificationTypeCreate, SpecificationTypeUpdate

router = APIRouter(prefix="/specification-types", tags=["specification_types"])


@router.post("/", response_model=SpecificationType, status_code=status.HTTP_201_CREATED)
async def add_specification_type(
        specification_type_data: SpecificationTypeCreate,
        db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли уже specification_type с таким именем
    result = await db.execute(
        select(SpecificationTypeModel).filter(SpecificationTypeModel.name == specification_type_data.name)
    )
    existing_specification_type = result.scalar_one_or_none()

    if existing_specification_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SpecificationType with this name already exists"
        )

    db_specification_type = SpecificationTypeModel(**specification_type_data.dict())
    db.add(db_specification_type)
    await db.commit()
    await db.refresh(db_specification_type)
    return db_specification_type


@router.get("/", response_model=List[SpecificationType])
async def get_all_specification_types(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationTypeModel).offset(skip).limit(limit)
    )
    specification_types = result.scalars().all()
    return specification_types


@router.get("/{specification_type_id}", response_model=SpecificationType)
async def get_specification_type(
        specification_type_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationTypeModel).filter(SpecificationTypeModel.id == specification_type_id)
    )
    specification_type = result.scalar_one_or_none()

    if not specification_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SpecificationType not found"
        )
    return specification_type


@router.put("/{specification_type_id}", response_model=SpecificationType)
async def update_specification_type(
        specification_type_id: int,
        specification_type_data: SpecificationTypeUpdate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationTypeModel).filter(SpecificationTypeModel.id == specification_type_id)
    )
    db_specification_type = result.scalar_one_or_none()

    if not db_specification_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SpecificationType not found"
        )

    # Проверяем, не занято ли новое имя другим specification_type
    if specification_type_data.name != db_specification_type.name:
        result = await db.execute(
            select(SpecificationTypeModel).filter(
                SpecificationTypeModel.name == specification_type_data.name,
                SpecificationTypeModel.id != specification_type_id
            )
        )
        existing_specification_type = result.scalar_one_or_none()

        if existing_specification_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SpecificationType with this name already exists"
            )

    # Обновляем поля
    for field, value in specification_type_data.dict(exclude_unset=True).items():
        setattr(db_specification_type, field, value)

    await db.commit()
    await db.refresh(db_specification_type)
    return db_specification_type


@router.delete("/{specification_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specification_type(
        specification_type_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationTypeModel).filter(SpecificationTypeModel.id == specification_type_id)
    )
    db_specification_type = result.scalar_one_or_none()

    if not db_specification_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SpecificationType not found"
        )

    await db.delete(db_specification_type)
    await db.commit()
    return None