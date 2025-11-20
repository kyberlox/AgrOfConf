from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..model.database import get_db
from ..model.specification import Specification as SpecificationModel
from ..model.parameter import Parameter as ParameterModel
from ..model.specification_type import SpecificationType as SpecificationTypeModel
from ..schema.specification import Specification, SpecificationCreate, SpecificationUpdate

router = APIRouter(prefix="/specifications", tags=["specifications"])


@router.post("/", response_model=Specification, status_code=status.HTTP_201_CREATED)
async def add_specification(
        specification_data: SpecificationCreate,
        db: AsyncSession = Depends(get_db)
):
    # Проверяем существование parameter
    result = await db.execute(
        select(ParameterModel).filter(ParameterModel.id == specification_data.parameter_id)
    )
    parameter = result.scalar_one_or_none()
    if not parameter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parameter not found"
        )

    # Проверяем существование specification_type
    result = await db.execute(
        select(SpecificationTypeModel).filter(SpecificationTypeModel.id == specification_data.specification_type_id)
    )
    specification_type = result.scalar_one_or_none()
    if not specification_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SpecificationType not found"
        )

    db_specification = SpecificationModel(**specification_data.dict())
    db.add(db_specification)
    await db.commit()
    await db.refresh(db_specification)
    return db_specification


@router.get("/{specification_id}", response_model=Specification)
async def get_specification(
        specification_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationModel).filter(SpecificationModel.id == specification_id)
    )
    specification = result.scalar_one_or_none()

    if not specification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specification not found"
        )
    return specification


@router.put("/{specification_id}", response_model=Specification)
async def update_specification(
        specification_id: int,
        specification_data: SpecificationUpdate,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationModel).filter(SpecificationModel.id == specification_id)
    )
    db_specification = result.scalar_one_or_none()

    if not db_specification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specification not found"
        )

    # Проверяем существование parameter (если изменился)
    if specification_data.parameter_id != db_specification.parameter_id:
        result = await db.execute(
            select(ParameterModel).filter(ParameterModel.id == specification_data.parameter_id)
        )
        parameter = result.scalar_one_or_none()
        if not parameter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parameter not found"
            )

    # Проверяем существование specification_type (если изменился)
    if specification_data.specification_type_id != db_specification.specification_type_id:
        result = await db.execute(
            select(SpecificationTypeModel).filter(SpecificationTypeModel.id == specification_data.specification_type_id)
        )
        specification_type = result.scalar_one_or_none()
        if not specification_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SpecificationType not found"
            )

    # Обновляем поля
    for field, value in specification_data.dict(exclude_unset=True).items():
        setattr(db_specification, field, value)

    await db.commit()
    await db.refresh(db_specification)
    return db_specification


@router.delete("/{specification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specification(
        specification_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationModel).filter(SpecificationModel.id == specification_id)
    )
    db_specification = result.scalar_one_or_none()

    if not db_specification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specification not found"
        )

    await db.delete(db_specification)
    await db.commit()
    return None


# Дополнительные методы для удобства

@router.get("/parameter/{parameter_id}", response_model=List[Specification])
async def get_specifications_by_parameter(
        parameter_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationModel).filter(SpecificationModel.parameter_id == parameter_id)
    )
    specifications = result.scalars().all()
    return specifications


@router.get("/specification-type/{specification_type_id}", response_model=List[Specification])
async def get_specifications_by_type(
        specification_type_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SpecificationModel).filter(SpecificationModel.specification_type_id == specification_type_id)
    )
    specifications = result.scalars().all()
    return specifications