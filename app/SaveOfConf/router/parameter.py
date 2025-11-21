import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import aiofiles

from ..model.database import get_db
from ..model.parameter import Parameter as ParameterModel
from ..model.product import Product as ProductModel
from ..model.parameter_type import ParameterType as ParameterTypeModel
from ..schema.parameter import Parameter, ParameterCreate, ParameterUpdate

router = APIRouter(prefix="/parameters", tags=["parameters"])


@router.post("/", response_model=Parameter, status_code=status.HTTP_201_CREATED)
async def add_parameter(
        parameter_data: ParameterCreate,
        db: AsyncSession = Depends(get_db)
):
    # Проверяем существование product
    result = await db.execute(
        select(ProductModel).filter(ProductModel.id == parameter_data.product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Проверяем существование parameter_type
    result = await db.execute(
        select(ParameterTypeModel).filter(ParameterTypeModel.id == parameter_data.parameter_type_id)
    )
    parameter_type = result.scalar_one_or_none()
    if not parameter_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ParameterType not found"
        )

    db_parameter = ParameterModel(**parameter_data.dict())
    db.add(db_parameter)
    await db.commit()
    await db.refresh(db_parameter)
    return db_parameter


@router.get("/{parameter_id}", response_model=Parameter)
async def get_parameter(
        parameter_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterModel).filter(ParameterModel.id == parameter_id)
    )
    parameter = result.scalar_one_or_none()

    if not parameter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parameter not found"
        )
    return parameter


@router.put("/{parameter_id}", response_model=Parameter)
async def update_parameter(
        parameter_id: int,
        parameter_data: ParameterUpdate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterModel).filter(ParameterModel.id == parameter_id)
    )
    db_parameter = result.scalar_one_or_none()

    if not db_parameter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parameter not found"
        )

    # Проверяем существование product (если изменился)
    if parameter_data.product_id != db_parameter.product_id:
        result = await db.execute(
            select(ProductModel).filter(ProductModel.id == parameter_data.product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

    # Проверяем существование parameter_type (если изменился)
    if parameter_data.parameter_type_id != db_parameter.parameter_type_id:
        result = await db.execute(
            select(ParameterTypeModel).filter(ParameterTypeModel.id == parameter_data.parameter_type_id)
        )
        parameter_type = result.scalar_one_or_none()
        if not parameter_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ParameterType not found"
            )

    # Обновляем поля
    for field, values in parameter_data.dict(exclude_unset=True).items():
        setattr(db_parameter, field, values)

    await db.commit()
    await db.refresh(db_parameter)
    return db_parameter


@router.delete("/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter(
        parameter_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterModel).filter(ParameterModel.id == parameter_id)
    )
    db_parameter = result.scalar_one_or_none()

    if not db_parameter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parameter not found"
        )

    await db.delete(db_parameter)
    await db.commit()
    return None

# Дополнительный метод для получения всех параметров продукта
@router.get("/product/{product_id}", response_model=List[Parameter])
async def get_parameters_by_product(
        product_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ParameterModel).filter(ParameterModel.product_id == product_id)
    )
    parameters = result.scalars().all()
    return parameters