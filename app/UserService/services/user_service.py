from ..repo.user_repo import UserRepo
from sqlalchemy.ext.asyncio import AsyncSession
from ..model.Users import Users
from typing import Optional
from sqlalchemy import select

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepo(db)

    async def create_user(self, user_data: dict) -> Users:
        """Создает пользователя"""
        user = Users(**user_data)
        return await self.user_repo.add(user)

    async def update_user(self, user_id: int, user_data: dict) -> Optional[Users]:
        """Обновляет пользователя"""
        return await self.user_repo.update(user_id, user_data)
    
    async def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя"""
        user = await self.user_repo.get_by_id(user_id)
        if user:
            await self.user_repo.delete(user)
            return True
        return False
    
    async def get_user(self, user_id: int) -> Optional[Users]:
        """Возвращает пользователя по id"""
        return await self.user_repo.get_by_id(user_id)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[Users]:
        """Возвращает всех пользователей"""
        return await self.user_repo.get_all(skip, limit)

    async def get_users_in_product(self, product_id: int) -> list[Users]:
        """Возвращает всех пользователей, имеющих доступ к продукту"""
        from ..model.Roots import Roots
        # from ..repo.roots_repo import RootsRepo
        # roots_repo = RootsRepo(self.user_repo.db)
        # users_id = await roots_repo.get_product_users(product_id)
        
        # if not users_id:
        #     return []
        # stmt = select(Users).where(Users.id.in_(users_id))
        # res = await self.user_repo.db.execute(stmt)
        stmt = select(Users, Roots.id).join(
            Roots, Users.id == Roots.user_id
        ).where(Roots.product_id == product_id)
        res = await self.user_repo.db.execute(stmt)
        return res.scalars().all()