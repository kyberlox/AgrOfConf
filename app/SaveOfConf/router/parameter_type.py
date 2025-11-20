import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..model.database import get_db
from ..model.parameter_type import ParameterType as ParameterTypeModel
from ..schema.parameter_type import ParameterType, ParameterTypeCreate, ParameterTypeUpdate

router = APIRouter(prefix="/parameter-types", tags=["parameter_types"])


@router.post("/", response_model=ParameterType, status_code=status.HTTP_201_CREATED)
async def add_parameter_type(
        parameter_type_data: ParameterTypeCreate,
        db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли уже parameter_type с таким именем
    result = await db.execute(
        select(ParameterTypeModel).filter(ParameterTypeModel.name == parameter_type_data.name)
    )
    existing_parameter_type = result.scalar_one_or_none()

    if existing_parameter_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ParameterType with this name already exists"
        )

    db_parameter_type = ParameterTypeModel(**parameter_type_data.dict())
    db.add(db_parameter_type)
    await db.commit()
    await db.refresh(db_parameter_type)
    return db_parameter_type


@router.get("/", response_model=List[ParameterType])
async def get_all_parameter_types(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterTypeModel).offset(skip).limit(limit)
    )
    parameter_types = result.scalars().all()
    return parameter_types


@router.get("/{parameter_type_id}", response_model=ParameterType)
async def get_parameter_type(
        parameter_type_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterTypeModel).filter(ParameterTypeModel.id == parameter_type_id)
    )
    parameter_type = result.scalar_one_or_none()

    if not parameter_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ParameterType not found"
        )
    return parameter_type


@router.put("/{parameter_type_id}", response_model=ParameterType)
async def update_parameter_type(
        parameter_type_id: int,
        parameter_type_data: ParameterTypeUpdate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterTypeModel).filter(ParameterTypeModel.id == parameter_type_id)
    )
    db_parameter_type = result.scalar_one_or_none()

    if not db_parameter_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ParameterType not found"
        )

    # Проверяем, не занято ли новое имя другим parameter_type
    if parameter_type_data.name != db_parameter_type.name:
        result = await db.execute(
            select(ParameterTypeModel).filter(
                ParameterTypeModel.name == parameter_type_data.name,
                ParameterTypeModel.id != parameter_type_id
            )
        )
        existing_parameter_type = result.scalar_one_or_none()

        if existing_parameter_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ParameterType with this name already exists"
            )

    # Обновляем поля
    for field, value in parameter_type_data.dict(exclude_unset=True).items():
        setattr(db_parameter_type, field, value)

    await db.commit()
    await db.refresh(db_parameter_type)
    return db_parameter_type


@router.delete("/{parameter_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter_type(
        parameter_type_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterTypeModel).filter(ParameterTypeModel.id == parameter_type_id)
    )
    db_parameter_type = result.scalar_one_or_none()

    if not db_parameter_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ParameterType not found"
        )

    await db.delete(db_parameter_type)
    await db.commit()
    return None