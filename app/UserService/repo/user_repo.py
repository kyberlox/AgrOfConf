from sqlalchemy.ext.asyncio import AsyncSession
from .base_repo import BaseRepo

class UserRepo(BaseRepo):
    def __init__(self, db: AsyncSession):
        from ..model.Users import Users
        super().__init__(Users, db)

    """
    Сюда прописать доп методы для работы с таблицей Users,
    которых нет в BaseRepo
    """