from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Query


from ..repo.abstracktion_repo import DatabaseStatistic
from ..repo.elastic_statistic_repo import ElasticStatisticRepo
from ..set.settings import SELECTION_INDEX
from ..model.database import get_statistic_db

from ..schema.selection_schema import SelectionData, SelectionResponse

from app.UserService.utils.auth_utils import get_user_id_by_session_id


router = APIRouter(prefix="/selection_statistic", tags=["Сбор статистики подбора"])


class SelectionRouter:
    """
    Класс‑роутер для работы со статистикой подбора.
    Принимает любую реализацию DatabaseStatistic (Elasticsearch, Postgres, Mongo и т.д.).
    """

    def __init__(self, repo: DatabaseStatistic):
        self.repo = repo

    async def save_selection(self, data: SelectionData) -> SelectionResponse:
        """Сохранить запись о подборе."""
        try:
            result = await self.repo.save(data)
            return SelectionResponse(success=True, data=result)
        except Exception as e:
            return SelectionResponse(success=False, error=str(e))

    async def delete_selection(self, record_id: Union[str, int]) -> SelectionResponse:
        """Удалить запись по идентификатору."""
        try:
            result = await self.repo.delete(record_id)
            return SelectionResponse(success=True, data=result)
        except Exception as e:
            return SelectionResponse(success=False, error=str(e))

    async def get_all_selection(
        self,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи подбора с пагинацией."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_selection_by_id(self, record_id: Union[str, int]) -> Any:
        """Получить запись по идентификатору."""
        return await self.repo.get_by_id(record_id)

    async def get_selection_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи для указанного пользователя с пагинацией."""
        return await self.repo.get_by_user_id(user_id, skip=skip, limit=limit)

    async def get_selection_by_product_id(
        self,
        product_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи для указанного продукта с пагинацией."""
        return await self.repo.get_by_product_id(product_id, skip=skip, limit=limit)
    
    async def get_selection_by_key_and_value(
        self,
        key: str,
        value: str,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи по ключу и значению с пагинацией."""
        return await self.repo.search_by_key_and_value(key, value, skip=skip, limit=limit) 
    
    async def get_by_value(self, value: str, skip: int = 0, limit: Optional[int] = None,) -> List[Any]:
        """Получить все записи по значению."""
        return await self.repo.search_all_fields(value, skip=skip, limit=limit)
    
    async def get_number_document(self, user_id: int) -> int:
        """Получить порядковый номер документа для указанного пользователя."""
        return await self.repo.last_document_number(user_id)


# ──────────────────────────────────────────────
# FastAPI‑эндпоинты (точки входа)
# ──────────────────────────────────────────────

def get_selection_router() -> SelectionRouter:
    """
    Фабрика‑зависимость для SelectionRouter.
    Использует собственный клиент StatisticsService (по умолчанию Elasticsearch).
    """
    db = get_statistic_db()
    repo: DatabaseStatistic = ElasticStatisticRepo(SELECTION_INDEX, db)
    return SelectionRouter(repo=repo)


@router.post("/selection", response_model=SelectionResponse)
async def upload_selection(
    data: SelectionData,
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Загрузить новую запись подбора."""
    return await router_instance.save_selection(data)


@router.delete("/selection/{record_id}", response_model=SelectionResponse)
async def delete_selection(
    record_id: str,
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Удалить запись подбора по ID."""
    return await router_instance.delete_selection(record_id)


@router.get("/selection")
async def get_all_selection(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: Optional[int] = Query(None, ge=1, description="Максимальное количество записей"),
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Получить все записи подбора с пагинацией."""
    return await router_instance.get_all_selection(skip=skip, limit=limit)


@router.get("/selection/by-user/{user_id}")
async def get_selection_by_user(
    user_id: Optional[int],
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: Optional[int] = Query(None, ge=1, description="Максимальное количество записей"),
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Получить все записи подбора для пользователя с пагинацией."""
    return await router_instance.get_selection_by_user_id(
        user_id, skip=skip, limit=limit,
    )


@router.get("/selection/by-product/{product_id}")
async def get_selection_by_product(
    product_id: int,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: Optional[int] = Query(None, ge=1, description="Максимальное количество записей"),
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Получить все записи подбора для продукта с пагинацией."""
    return await router_instance.get_selection_by_product_id(
        product_id, skip=skip, limit=limit,
    )


@router.get("/selection/{record_id}")
async def get_selection_by_id(
    record_id: str,
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Получить запись подбора по ID."""
    return await router_instance.get_selection_by_id(record_id)

@router.get("/search_by_key_and_value", status_code=200)
async def search_by_key_and_value(
    key: str, 
    value: str,
    skip: int = 0,
    limit: int = 100,
    router_instance: SelectionRouter = Depends(get_selection_router)
):
    """Поиск по ключу и значению."""
    return await router_instance.search_by_key_and_value(key, value, skip=skip, limit=limit)

@router.get("/search_by_value", status_code=200)
async def search_by_value(
    value: str,
    skip: int = 0,
    limit: int = 100,
    router_instance: SelectionRouter = Depends(get_selection_router)
):
    """Поиск по значению."""
    return await router_instance.get_by_value(value, skip=skip, limit=limit)