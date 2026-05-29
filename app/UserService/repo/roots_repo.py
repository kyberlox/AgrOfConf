from sqlalchemy.ext.asyncio import AsyncSession
from .base_repo import BaseRepo
from sqlalchemy import select

class RootsRepo(BaseRepo):
    def __init__(self, db: AsyncSession):
        from ..model.Roots import Roots
        super().__init__(Roots, db)
    
    async def has_user_access(self, user_id: int, product_id: int) -> bool:
        """Проверяет есть ли у пользователя доступ к продукту. Для Dependency"""
        stmt = select(self.model).where(self.model.user_id == user_id, self.model.product_id == product_id)
        res = await self.db.execute(stmt)
        is_access = res.scalar_one_or_none()
        if is_access:
            return True
        return False
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверяет является ли пользователь админом"""
        stmt = select(self.model).where(self.model.user_id == user_id, self.model.admin == True)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            return True
        return False
    
    async def get_product_users(self, product_id: int) -> list[int]:
        """Возвращает список пользователей, имеющих доступ к продукту"""
        stmt = select(self.model.user_id).where(self.model.product_id == product_id)
        res_stmt = await self.db.execute(stmt)
        res = res_stmt.scalars().all()
        return res


        