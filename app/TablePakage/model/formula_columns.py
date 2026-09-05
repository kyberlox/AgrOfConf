"""
Лёгкая миграция схемы для новой системы формул.

`Base.metadata.create_all` создаёт таблицу один раз и НЕ добавляет новые колонки
в уже существующую. Поэтому колонка `formula_config` добавляется явным ALTER TABLE
при старте приложения.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def ensure_formula_config_column(db: AsyncSession) -> None:
    """Добавляет колонку formula_config в parameter_schemas, если её нет."""
    await db.execute(text(
        "ALTER TABLE parameter_schemas "
        "ADD COLUMN IF NOT EXISTS formula_config JSONB"
    ))
    await db.commit()