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