from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete

from .abstracktion_repo import DatabaseStatistic


# ──────────────────────────────────────────────
# Конвертеры между плоской RecognitionData
# и вложенной структурой PSQL RecognitionModel
# ──────────────────────────────────────────────

def _flat_to_psql(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует плоский dict (как RecognitionData) в структуру
    для ORM-модели RecognitionModel.
    """
    return {
        "product_id": data["product_id"],
        "user_id": data["user_id"],
        "product_info": {
            "product_name": data.get("product_name", ""),
            "product_description": data.get("product_description", ""),
            "product_manufacturer": data.get("product_manufacturer", ""),
            "product_image_url": data.get("product_image_url", ""),
        },
        "user_info": {
            "user_uuid": data.get("user_uuid", ""),
            "user_fio": data.get("user_fio", ""),
            "user_email": data.get("user_email", ""),
            "user_directorate": data.get("user_directorate", ""),
            "user_work_position": data.get("user_work_position", ""),
            "user_office": data.get("user_office", ""),
            "user_department": data.get("user_department", ""),
            "user_work_city": data.get("user_work_city", ""),
        },
        "parameters": data.get("parameters", {}),
        "total_coast": data.get("total_coast"),
        "created_at": data.get("date_search", datetime.utcnow()),
    }


def _psql_to_flat(record) -> Dict[str, Any]:
    """
    Преобразует ORM-объект RecognitionModel в плоский dict
    в формате RecognitionData.
    """
    product_info = record.product_info or {}
    user_info = record.user_info or {}

    return {
        "id": record.id,
        "product_id": record.product_id,
        "user_id": record.user_id,
        "product_name": product_info.get("product_name", ""),
        "product_description": product_info.get("product_description", ""),
        "product_manufacturer": product_info.get("product_manufacturer", ""),
        "product_image_url": product_info.get("product_image_url", ""),
        "user_uuid": user_info.get("user_uuid", ""),
        "user_fio": user_info.get("user_fio", ""),
        "user_email": user_info.get("user_email", ""),
        "user_directorate": user_info.get("user_directorate", ""),
        "user_work_position": user_info.get("user_work_position", ""),
        "user_office": user_info.get("user_office", ""),
        "user_department": user_info.get("user_department", ""),
        "user_work_city": user_info.get("user_work_city", ""),
        "parameters": record.parameters or {},
        "total_coast": getattr(record, "total_coast", None),
        "date_search": record.created_at,
    }


class PostgresStatisticRepo(DatabaseStatistic):
    def __init__(self, model, db):
        super().__init__(model, db)

    async def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сохраняет плоский RecognitionData в PSQL RecognitionModel.
        """
        psql_data = _flat_to_psql(data)
        model_columns = {c.name for c in self.model.__table__.columns}
        psql_data = {k: v for k, v in psql_data.items() if k in model_columns}
        new_node = self.model(**psql_data)
        self.db.add(new_node)
        await self.db.commit()
        await self.db.refresh(new_node)
        return _psql_to_flat(new_node)

    async def delete(self, id: int) -> bool:
        """Удаляет запись по id."""
        stmt = delete(self.model).where(self.model.id == id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def get_all(self, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Возвращает все записи с пагинацией, преобразованные в плоский формат."""
        stmt = select(self.model).order_by(self.model.created_at.desc()).offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [_psql_to_flat(r) for r in records]

    async def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Возвращает запись по id в плоском формате или None."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        return _psql_to_flat(record) if record else None

    async def get_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Возвращает все записи пользователя с пагинацией."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [_psql_to_flat(r) for r in records]

    async def get_by_product_id(
        self,
        product_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Возвращает все записи продукта с пагинацией."""
        stmt = (
            select(self.model)
            .where(self.model.product_id == product_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [_psql_to_flat(r) for r in records]