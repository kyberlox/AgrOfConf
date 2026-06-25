from typing import Optional, Union

from .abstracktion_repo import DatabaseStatistic


class MongoStatisticRepo(DatabaseStatistic):
    def __init__(self, model, db):
        super().__init__(model, db)

    def save(self, data):
        pass

    def delete(self, id: Union[str, int]):
        pass

    def get_all(self, skip: int = 0, limit: Optional[int] = None):
        pass

    def get_by_id(self, id: Union[str, int]):
        pass

    def get_by_user_id(self, user_id: int, skip: int = 0, limit: Optional[int] = None):
        pass

    def get_by_product_id(self, product_id: int, skip: int = 0, limit: Optional[int] = None):
        pass

    