"""
Миграция схемы для блоков параметров.

Таблица `parameter_blocks` создаётся автоматически через `Base.metadata.create_all`
(модель ParameterBlock зарегистрирована в модели __init__). Для уже существующей
таблицы `parameter_schemas` колонка `block_id` добавляется явным ALTER TABLE.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def ensure_blocks_schema(db: AsyncSession) -> None:
    """Добавляет колонки блоков: block_id в parameter_schemas и properties/description в parameter_blocks."""
    await db.execute(text(
        "ALTER TABLE parameter_schemas "
        "ADD COLUMN IF NOT EXISTS block_id INTEGER"
    ))
    await db.execute(text(
        "ALTER TABLE parameter_blocks "
        "ADD COLUMN IF NOT EXISTS properties JSONB DEFAULT '{}'::jsonb"
    ))
    await db.execute(text(
        "ALTER TABLE parameter_blocks "
        "ADD COLUMN IF NOT EXISTS description VARCHAR(1000)"
    ))
    await db.commit()