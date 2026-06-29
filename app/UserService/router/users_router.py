from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import select

from ..model.Users import Users
from ..services.user_service import UserService
from ..services.redis_service import RedisStorage
from app.TablePakage.model.database import get_db

router = APIRouter(prefix="/users", tags=["Пользователи"])

redis_storage = RedisStorage()


async def parse_user_data(data: dict) -> dict:
    """
    Извлекает нужные поля из входного JSON от Битрикс24
    """
    try:
        xml_id = data.get("XML_ID", "")
        if xml_id.startswith("ad|"):
            xml_id = xml_id[3:]  # убираем "ad|"

        return {
            "id": int(data["ID"]),
            "uuid": xml_id,
            "is_active": bool(data["ACTIVE"]),
            "last_name": data.get("LAST_NAME"),
            "name": data.get("NAME"),
            "second_name": data.get("SECOND_NAME"),
            "email": data.get("EMAIL"),
            "work_phone": data.get("UF_PHONE_INNER"),
            "directorate": (
                data["UF_USR_1696592324977"][0]
                if isinstance(data.get("UF_USR_1696592324977"), list) and data["UF_USR_1696592324977"]
                else None
            ),
            "department": (
                data["UF_USR_1705744824758"][0]
                if isinstance(data.get("UF_USR_1705744824758"), list) and data["UF_USR_1705744824758"]
                else None
            ),
            "work_position": data.get("WORK_POSITION"),
            "work_city": data.get("PERSONAL_CITY"),
            "office": int(data.get("UF_USR_1586854037086")),
            "photo": data.get("PERSONAL_PHOTO")
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Отсутствует обязательное поле: {e}")



@router.post("/create_user", status_code=201)
async def create_user(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Создаёт или обновляет пользователя по ID.
    Если пользователь с таким id уже есть — обновляет.
    """
    try:
        user_data = await parse_user_data(data)

        # Проверяем, существует ли пользователь
        service = UserService(db)
        user = await service.get_user(user_data["id"])

        if user:
            raise HTTPException(status_code=409, detail="Пользователь уже существует")
        
        # new_user = Users(**user_data)
        res_new_user = await service.create_user(user_data)
        
        session_id = f"user:{res_new_user.id}"
        redis_storage.save_session(session_id, user_data)

        return res_new_user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания пользователя: {str(e)}")


@router.get("/find_by/{user_id}", status_code=200)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Получает пользователя по ID.
    Сначала проверяет Redis, потом БД.
    """
    try:
        service = UserService(db)
        user = await service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        return user
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка получения пользователя: {str(e)}")


@router.get("/all", status_code=200)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Получает список пользователей с фильтрами.
    Асинхронная версия с использованием AsyncSession.
    """
    try:
        service = UserService(db)
        users = await service.get_all_users(skip, limit)
        return users
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка пользователей: {str(e)}")
   

@router.delete("/delete_by/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Удаляет пользователя из БД и Redis.
    """
    try:
        service = UserService(db)
        success = await service.delete_user(user_id)
        return success
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления пользователя: {str(e)}")

@router.get("/product_users", status_code=200)
async def get_product_users(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Возвращает всех пользователей, имеющих доступ к продукту"""
    try:
        from app.TablePakage.model.product import Product
        stmt = select(Product).where(Product.id == product_id)
        product = await db.execute(stmt)
        if not product.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Продукт не найден")
        service = UserService(db)
        users = await service.get_users_in_product(product_id)
        return users
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка получения пользователей с правами доступа к продукту: {str(e)}")