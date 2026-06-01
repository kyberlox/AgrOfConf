from ..services.redis_service import RedisStorage
from typing import Optional
import httpx

redis_storage = RedisStorage()

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