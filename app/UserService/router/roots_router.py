from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..services.root_service import RootService
from app.TablePakage.model.database import get_db

router = APIRouter(prefix="/roots", tags=["Права доступа"])

@router.post("/create_new_root", status_code=201)
async def create_new_root(
    user_id: int,
    product_id: int,
    admin: Optional[bool] = False,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = RootService(db)
        new_root = await service.create_root(user_id, product_id, admin)
        return new_root
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка добавления новых прав доступа{str(e)}")

@router.get("/access_base", status_code=200)
async def get_access_base(
    user_id: int,
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = RootService(db)
        is_access = await service.user_has_access(user_id, product_id)
        return is_access
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка проверки базового доступа: {str(e)}")

@router.get("/access_admin", status_code=200)
async def get_access_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = RootService(db)
        is_admin = await service.has_user_admin_access(user_id)
        return is_admin
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка проверки прав администратора: {str(e)}")
    
@router.delete("/delete_root", status_code=200)
async def delete_root(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = RootService(db)
        sell = await service.delete_root(id)
        return sell
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления прав доступа: {str(e)}")