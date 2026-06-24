from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
import httpx

from ..model.Users import Users
from .users_router import parse_user_data
from ..services.redis_service import RedisStorage
from app.TablePakage.model.database import get_db
from ..utils.auth_utils import validate_users_sessions, create_session

router = APIRouter(prefix="/auth", tags=["Авторизация"])

redis_storage = RedisStorage()

async def user_info_by_session_id(token: str):
    # url = "http://intranet.emk.org.ru/api/auth_router/check"
    url = "http://intranet.emk.org.ru/api/auth_router/check"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, cookies={'session_id': token})
        if res.status_code == 200:
            return json.loads(res.text)
    return None


@router.get("/redirect")
async def get_user(
    session_id: str, 
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Получает редирект с Интранета.
    Проверяет корректность сессии.
    Проверяет наличие пользователя в БД.
    Если пользователь найден, возвращает его на главную.
    Если нет, создаем пользователя и возвращаем на главную.
    """
    try:
        is_active = await user_info_by_session_id(session_id)
        if not is_active:
            raise HTTPException(status_code=401, detail="Неверный токен")
        
        is_auth = is_active.get('authenticated', False)
        if not is_auth:
            raise HTTPException(status_code=401, detail="Проверьте авторизацию в Интранете")
        
        user_id = int(is_active['user']['ID'])
        stmt = await db.execute(select(Users).filter(Users.id == user_id))
        user = stmt.scalar_one_or_none()
        if not user:
            user_data = await parse_user_data(is_active['user'])
            new_user = Users(**user_data)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
        
        # Проверяем создание сессии
        is_valid = await validate_users_sessions(user_id=user_id)
        
        session = await create_session(session_id, user_id)
        response.set_cookie(
            key="session_id", 
            value=session, 
            samesite="lax"
        )
        return RedirectResponse(url="/")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения пользователя: {str(e)}")
