"""FastAPI-dependencies для проверки прав доступа.

- `get_current_user_id` — базовая авторизация: user_id по сессии.
- `require_product_access(product_id)` — «обычные» права: у пользователя есть
  доступ к продукту (запись в roots для продукта либо права администратора).
- `require_admin` — права администратора (в roots есть запись с admin=True).

user_id в каждом случае берётся из сессии через dependency
`get_user_id_by_session_id`.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.TablePakage.model.database import get_db
from ..model.Roots import Roots
from ..model.Users import Users
from .auth_utils import get_user_id_by_session_id


async def get_current_user_id(
    user_id: int = Depends(get_user_id_by_session_id),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Базовая авторизация: возвращает user_id авторизованного (активного) пользователя."""
    res = await db.execute(select(Users).where(Users.id == user_id))
    user = res.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь не найден или неактивен",
        )
    return user_id


async def require_product_access(
    product_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Обычные права: доступ к конкретному продукту.

    Доступ есть, если у пользователя есть запись в roots для этого продукта
    либо запись с admin=True (админ имеет доступ ко всем продуктам).
    """
    res = await db.execute(
        select(Roots).where(
            Roots.user_id == user_id,
            (Roots.product_id == product_id) | (Roots.admin.is_(True)),
        )
    )
    if res.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к продукту",
        )
    return user_id


async def require_admin(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Права администратора: существует запись roots с admin=True у данного пользователя."""
    res = await db.execute(
        select(Roots).where(Roots.user_id == user_id, Roots.admin.is_(True))
    )
    if res.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав: требуется администратор",
        )
    return user_id