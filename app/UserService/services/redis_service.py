import redis
import json
import os
from typing import Optional, Dict, Any
from datetime import timedelta

class RedisStorage:

    def __init__(
        self,
        session_ttl: timedelta = timedelta(hours=1) 
    ):
        self.session_ttl = session_ttl  # время жизни сессии
        try:
            redis_host = "redis"
            redis_port = 6379
            redis_db = 0
            redis_password = os.getenv("pswd")
            self.redis_client = redis.StrictRedis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Проверка подключения
            self.redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Не удалось подключиться к Redis: {e}")
        except Exception as e:
            raise RuntimeError(f"Ошибка инициализации Redis: {e}")

    def save_session(self, session_id: str, user_id: int) -> bool:
        """
        Сохраняет сессию в Redis.
        :param session_id: str — уникальный идентификатор сессии
        :param data: dict — данные сессии
        :return: bool — успех операции
        """
        if not session_id or not isinstance(user_id, int):
            return False
        try:
            self.redis_client.setex(
                name=session_id,
                time=int(self.session_ttl.total_seconds()),
                value=str(user_id)
            )
            return True
        except Exception as e:
            print(f"Ошибка сохранения сессии {session_id}: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает user_id из Redis.
        :param session_id: str
        :return: dict или None
        """
        if not session_id:
            return None
        try:
            user_id = self.redis_client.get(session_id)
            return int(user_id) if user_id is not None else None
        except Exception as e:
            print(f"Ошибка получения сессии {session_id}: {e}")
            return None

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Полностью обновляет данные сессии (перезаписывает).
        :param session_id: str
        :param data: новое значение (dict)
        :return: bool
        """
        return self.save_session(session_id, data)

    def delete_session(self, session_id: str) -> bool:
        """
        Удаляет сессию.
        :param session_id: str
        :return: bool
        """
        try:
            deleted_count = self.redis_client.delete(session_id)
            return deleted_count > 0
        except Exception as e:
            print(f"Ошибка удаления сессии {session_id}: {e}")
            return False

    def update_session_ttl(self, session_id: str, ttl: timedelta = None) -> bool:
        """
        Обновляет TTL сессии (например, при активности пользователя).
        :param session_id: str
        :param ttl: новое время жизни (по умолчанию — как в __init__)
        :return: bool
        """
        ttl = ttl or self.session_ttl
        try:
            result = self.redis_client.expire(session_id, int(ttl.total_seconds()))
            return result
        except Exception as e:
            print(f"Ошибка обновления TTL для {session_id}: {e}")
            return False

    def get_ttl(self, session_id: str) -> int:
        """Возвращает TTL в секундах. -1 — нет таймаута, -2 — ключ не существует."""
        try:
            return self.redis_client.ttl(session_id)
        except Exception:
            return -2

    def expire_session(self, session_id: str, ttl: int) -> bool:
        """Продлевает время жизни сессии."""
        try:
            return self.redis_client.expire(session_id, ttl)
        except Exception:
            return False

    def find_in_set(self, key: str) -> list:
        try:
            return self.redis_client.smembers(key)
        except redis.RedisError as e:
            return []

    def add_to_set(self, key: str, value: str) -> bool:
        """
        Добавление значения в множество
        
        :param key: Ключ множества
        :param value: Значение
        :return: True если успешно
        """
        try:
            return bool(self.redis_client.sadd(key, value))
        except redis.RedisError as e:
            return False
    
    def remove_from_set(self, key: str, value: str) -> bool:
        """
        Удаление значения из множества
        
        :param key: Ключ множества
        :param value: Значение
        :return: True если успешно
        """
        try:
            return bool(self.redis_client.srem(key, value))
        except redis.RedisError as e:
            return False