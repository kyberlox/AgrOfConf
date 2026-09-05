from ..repo.roots_repo import RootsRepo
from ..model.Roots import Roots
from sqlalchemy.ext.asyncio import AsyncSession

class RootService:
    def __init__(self, db: AsyncSession):
        self.repo = RootsRepo(db)

    async def create_root(self, user_id: int, product_id: int, admin: bool=False) -> Roots:
        """Создает запись в таблице Roots"""
        is_access = await self.repo.has_user_access(user_id, product_id)
        if is_access:
            return None
        
        is_admin = await self.repo.is_admin(user_id)
        if is_admin:
            return None
        root = Roots(user_id=user_id, product_id=product_id, admin=admin)
        return await self.repo.add(root)
    
    async def delete_root(self, id: int) -> bool:
        """Удаляет запись из таблицы Roots"""
        is_exist = await self.repo.get_by_id(id)
        if not is_exist:
            return False
        await self.repo.delete(is_exist)
        return True
    
    async def user_has_access(self, user_id: int, product_id: int) -> bool:
        """Проверяет есть ли у пользователя доступ к продукту"""
        return await self.repo.has_user_access(user_id, product_id)
    
    async def has_user_admin_access(self, user_id: int) -> bool:
        """Проверяет является ли пользователь админом"""
        return await self.repo.is_admin(user_id)