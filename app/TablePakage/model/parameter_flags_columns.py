"""
Миграция флагов параметров (editable и пр.).

Для уже существующей таблицы `parameter_schemas` новые колонки добавляются
явным ALTER TABLE при старте приложения.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def ensure_parameter_flags(db: AsyncSession) -> None:
    """Добавляет колонку editable в parameter_schemas, если её нет."""
    await db.execute(text(
        "ALTER TABLE parameter_schemas "
        "ADD COLUMN IF NOT EXISTS editable BOOLEAN DEFAULT TRUE"
    ))
    await db.commit()