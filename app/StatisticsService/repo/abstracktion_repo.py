from abc import ABC, abstractmethod
from typing import Optional, Union


class DatabaseStatistic(ABC):
    def __init__(self, model, db):
        self.model = model
        self.db = db

    """Абстракция для работы с базой данных"""
    @abstractmethod
    def save(self, data):
        pass

    @abstractmethod
    def delete(self, id: Union[str, int]):
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: Optional[int] = None):
        pass

    @abstractmethod
    def get_by_id(self, id: Union[str, int]):
        pass



