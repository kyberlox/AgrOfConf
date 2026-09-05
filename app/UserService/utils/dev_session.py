"""
DEV-сессия для локального тестирования интерфейса (максимальные права).

ВКЛЮЧЕНИЕ/ОТКЛЮЧЕНИЕ — через переменные окружения в .env:
    DEV_SESSION_ENABLED=true   # включить dev-сессию (по умолчанию: true)
    DEV_SESSION_ENABLED=false  # выключить — приложение вернётся к штатной авторизации
    DEV_USER_ID=4133           # id dev-пользователя (по умолчанию: 4133)

При старте приложения, если dev-сессия включена, в БД создаются/обновляются
dev-пользователь и admin-корень, а `get_user_id_by_session_id` всегда возвращает
его id. Благодаря этому `users/find_by`, `roots/access_admin` и статистика по
user_id работают штатно, давая пользователю максимальный доступ.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.Users import Users
from ..model.Roots import Roots

load_dotenv()

# По умолчанию dev-сессия ВКЛЮЧЕНА (удобно для разработки). Для отключения
# установите DEV_SESSION_ENABLED=false в .env.
_DEV_ENABLED = os.getenv("DEV_SESSION_ENABLED", "true").strip().lower() in (
    "1", "true", "yes", "on",
)
DEV_USER_ID = int(os.getenv("DEV_USER_ID", "4133"))


def is_dev_enabled() -> bool:
    return _DEV_ENABLED


def dev_user_id() -> int:
    return DEV_USER_ID


def dev_user_dict() -> dict:
    """Данные dev-пользователя (структура соответствует модели Users)."""
    return {
        "id": DEV_USER_ID,
        "uuid": f"dev-{DEV_USER_ID}",
        "is_active": True,
        "last_name": "Тестовый",
        "name": "Администратор",
        "second_name": "Dev",
        "email": "dev@localhost",
        "work_phone": "",
        "directorate": "ИТ",
        "department": "Разработка",
        "work_position": "Администратор",
        "work_city": "Самара",
        "office": 1,
        "photo": None,
    }


async def ensure_dev_user(db: AsyncSession) -> None:
    """
    Создаёт (или оставляет существующего) dev-пользователя и admin-корень в БД.
    Ничего не делает, если dev-сессия отключена.
    """
    if not is_dev_enabled():
        return

    # Пользователь
    result = await db.execute(select(Users).where(Users.id == DEV_USER_ID))
    user = result.scalar_one_or_none()
    if user is None:
        db.add(Users(**dev_user_dict()))
        await db.commit()

    # Admin-корень (максимальные права)
    root_result = await db.execute(
        select(Roots).where(
            Roots.user_id == DEV_USER_ID,
            Roots.admin.is_(True),
        )
    )
    root = root_result.scalars().first()
    if root is None:
        db.add(Roots(user_id=DEV_USER_ID, admin=True, product_id=None))
        await db.commit()