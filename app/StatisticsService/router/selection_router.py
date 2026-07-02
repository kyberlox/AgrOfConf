from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Query


from ..repo.abstracktion_repo import DatabaseStatistic
from ..repo.elastic_statistic_repo import ElasticStatisticRepo
from ..set.settings import SELECTION_INDEX
from ..model.database import get_statistic_db

from ..schema.selection_schema import SelectionData, SelectionResponse, UpdateStatusRequest, StatisticsResponse

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

    async def update_selection_status(
        self,
        record_id: Union[str, int],
        status: str,
    ) -> SelectionResponse:
        """Обновить статус документа."""
        try:
            result = await self.repo.update_status(record_id, status)
            return SelectionResponse(success=True, data=result)
        except Exception as e:
            return SelectionResponse(success=False, error=str(e))

    async def get_all_selection(
        self,
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        ko_users: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи подбора с пагинацией."""
        return await self.repo.get_all(
            user_id=user_id,
            product_id=product_id,
            status=status,
            ko_users=ko_users,
            date_to=date_to,
            date_from=date_from,
            skip=skip,
            limit=limit,
        )

    async def get_selection_by_id(self, record_id: Union[str, int]) -> Any:
        """Получить запись по идентификатору."""
        return await self.repo.get_by_id(record_id)
    
    async def get_selection_by_key_and_value(
        self,
        key: str,
        value: str,
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        ko_users: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи по ключу и значению с пагинацией."""
        return await self.repo.search_by_key_and_value(
            key=key,
            value=value,
            user_id=user_id,
            product_id=product_id,
            status=status,
            ko_users=ko_users,
            date_to=date_to,
            date_from=date_from,
            skip=skip,
            limit=limit,
        ) 
    
    async def get_by_value(
        self,
        value: str,
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        ko_users: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи по значению с опциональными фильтрами."""
        return await self.repo.search_all_fields(
            value,
            user_id=user_id,
            product_id=product_id,
            status=status,
            ko_users=ko_users,
            date_to=date_to,
            date_from=date_from,
            skip=skip,
            limit=limit,
        )
    
    async def get_statistics(
        self,
        user_id: Optional[int] = None,
        ko_users: Optional[List[int]] = None,
    ) -> dict:
        """Получить статистику по документам."""
        return await self.repo.get_statistics(
            user_id=user_id,
            ko_users=ko_users,
        )

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


@router.put("/update_status", response_model=SelectionResponse)
async def update_selection_status(
    body: UpdateStatusRequest,
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Обновить статус документа подбора."""
    return await router_instance.update_selection_status(
        record_id=body.id,
        status=body.status,
    )


@router.get("/selection")
async def get_all_selection(
    user_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    ko_users: Optional[List[int]] = Query(None, description="Список ID пользователей"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: Optional[int] = Query(None, ge=1, description="Максимальное количество записей"),
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Получить все записи подбора с пагинацией."""
    return await router_instance.get_all_selection(
        user_id=user_id, 
        product_id=product_id, 
        status=status, 
        ko_users=ko_users, 
        date_from=date_from, 
        date_to=date_to, 
        skip=skip, limit=limit,
    )

@router.get("/metrics", status_code=200, response_model=StatisticsResponse)
async def get_selection_statistics(
    user_id: Optional[int] = Query(None, description="ID пользователя"),
    ko_users: Optional[List[int]] = Query(None, description="Список ID пользователей"),
    router_instance: SelectionRouter = Depends(get_selection_router),
):
    """Получить статистику по документам подбора."""
    return await router_instance.get_statistics(
        user_id=user_id,
        ko_users=ko_users,
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
    user_id: Optional[int] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    ko_users: Optional[List[int]] = Query(None, description="Список ID пользователей"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    router_instance: SelectionRouter = Depends(get_selection_router)
):
    """Поиск по ключу и значению."""
    return await router_instance.get_selection_by_key_and_value(
        key, value, 
        user_id=user_id,    
        product_id=product_id, 
        status=status, 
        ko_users=ko_users, 
        date_from=date_from, 
        date_to=date_to,
        skip=skip, limit=limit,
    )

@router.get("/search_by_value", status_code=200)
async def search_by_value(
    value: str,
    user_id: Optional[int] = Query(None, description="ID пользователя"),
    product_id: Optional[int] = Query(None, description="ID продукта"),
    status: Optional[str] = Query(None, description="Статус"),
    ko_users: Optional[List[int]] = Query(None, description="Список ID пользователей"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, description="Максимальное количество записей"),
    router_instance: SelectionRouter = Depends(get_selection_router)
):
    """Поиск по значению с опциональными фильтрами."""
    return await router_instance.get_by_value(
        value,
        user_id=user_id,
        product_id=product_id,
        status=status,
        ko_users=ko_users,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )

