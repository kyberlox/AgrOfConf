from ..services.redis_service import RedisStorage
from fastapi import Request, HTTPException, status
from typing import Optional
import httpx

redis_storage = RedisStorage()

async def get_user_id_by_session_id(request: Request):
    """Dependency для получения id пользователя по request.

    Если включена DEV-сессия (DEV_SESSION_ENABLED=true в .env) — всегда
    возвращается id dev-пользователя с максимальными правами (удобно для
    локального тестирования). Иначе — штатная проверка сессии в Redis.
    """
    from .dev_session import is_dev_enabled, dev_user_id

    if is_dev_enabled():
        return dev_user_id()

    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            auth_header = request.headers.get("session_id")
            if auth_header:
                session_id = auth_header
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        user_id = redis_storage.get_session(session_id=session_id)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        return user_id
    except HTTPException:
        raise

async def validate_users_sessions(user_id: int) -> bool:
    user_sessions_key = f"user_sessions:{user_id}"
    sessions_list = redis_storage.find_in_set(key=user_sessions_key)

    if not sessions_list:
        return True 
    
    for user_session in sessions_list:
        await delete_session(session_id=user_session, key=user_sessions_key)
    return True

async def create_session(session_id: str, user_id: int) -> bool:
    redis_storage.save_session(session_id=session_id, user_id=user_id)
    
    user_sessions_key = f"user_sessions:{'user_id'}"
    redis_storage.add_to_set(user_sessions_key, session_id)
    return True

async def delete_session(session_id: str, key: Optional[str] = None) -> None:
        """Удаление сессии"""
        user_id = redis_storage.get_session(session_id)
        
        redis_storage.remove_from_set(key, session_id)
        
        redis_storage.delete_session(session_id)

async def refresh_session_id(token: str):
    url = "http://intranet.emk.org.ru/api/auth_router/refresh"
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, cookies={'session_id': token})
        if res.status_code == 200:
            return json.loads(res.text)
    return None