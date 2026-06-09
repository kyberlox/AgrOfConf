from app.TablePakage.model.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

class BaseRepo:
    def __init__(self, model: Base, db: AsyncSession):
        self.model = model
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100):
        stmt = select(self.model).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_by_id(self, id: int):
        stmt = select(self.model).where(self.model.id == id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
    
    async def add(self, upload_model: Base):
        self.db.add(upload_model)
        await self.db.commit()
        await self.db.refresh(upload_model)
        return upload_model
    
    async def update(self, id: int, **kwargs):
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()
    
    async def delete(self, delete_model: Base):
        await self.db.delete(delete_model)
        await self.db.commit()

{
    "name": "Электронный прайс-лист на предохранительный клапан",
    "description": "",
    "manufacturer": "АО НПО Регулятор",
    "image_url": "/api/files/images/0823780a-d2f5-457b-9e9f-a7cebb5123ec.jpg",
    "id": 1,
    "image": "./static/images/0823780a-d2f5-457b-9e9f-a7cebb5123ec.jpg",
    "created_at": "2026-05-20T12:18:03.852014Z"
  }