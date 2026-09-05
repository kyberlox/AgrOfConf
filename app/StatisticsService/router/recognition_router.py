from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Query, HTTPException

from ..repo.abstracktion_repo import DatabaseStatistic
from ..repo.elastic_statistic_repo import ElasticStatisticRepo
from ..set.settings import RECOGNITION_INDEX
from ..model.database import get_statistic_db

from ..schema.recognition_schema import RecognitionData, RecognitionResponse

from app.UserService.utils.auth_utils import get_user_id_by_session_id

router = APIRouter(prefix="/recognition_statistic", tags=["Сбор статистики распознавания ОЛ"])


class RecognitionRouter:
    """
    Класс‑роутер для работы со статистикой распознавания.
    Принимает любую реализацию DatabaseStatistic (Elasticsearch, Postgres, Mongo и т.д.).
    """

    def __init__(self, repo: DatabaseStatistic):
        self.repo = repo

    async def save_recognition(self, data: RecognitionData) -> RecognitionResponse:
        """Сохранить запись о распознавании."""
        try:
            result = await self.repo.save(data)
            return RecognitionResponse(success=True, data=result)
        except Exception as e:
            return RecognitionResponse(success=False, error=str(e))

    async def delete_recognition(self, record_id: Union[str, int]) -> RecognitionResponse:
        """Удалить запись по идентификатору."""
        try:
            result = await self.repo.delete(record_id)
            return RecognitionResponse(success=True, data=result)
        except HTTPException as e:
            raise
        except Exception as e:
            return RecognitionResponse(success=False, error=str(e))

    async def get_all_recognition(
        self,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи распознавания с пагинацией."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_recognition_by_id(self, record_id: Union[str, int]) -> Any:
        """Получить запись по идентификатору."""
        try:
            return await self.repo.get_by_id(record_id)
        except HTTPException as e:
            raise
        except Exception as e:
            return RecognitionResponse(success=False, error=str(e))

    async def get_recognition_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи для указанного пользователя с пагинацией."""
        return await self.repo.get_by_user_id(user_id, skip=skip, limit=limit)

    async def get_recognition_by_product_id(
        self,
        product_id: int,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Получить все записи для указанного продукта с пагинацией."""
        return await self.repo.get_by_product_id(product_id, skip=skip, limit=limit)



def get_recognition_router() -> RecognitionRouter:
    """
    Фабрика‑зависимость для RecognitionRouter.
    Использует собственный клиент StatisticsService (по умолчанию Elasticsearch).
    При смене хранилища достаточно заменить клиент в ../model/database.py
    и/или репозиторий ниже.
    """
    db = get_statistic_db()
    repo: DatabaseStatistic = ElasticStatisticRepo(RECOGNITION_INDEX, db)
    return RecognitionRouter(repo=repo)


@router.post("/upload", response_model=RecognitionResponse)
async def upload_recognition(
    data: RecognitionData,
    router_instance: RecognitionRouter = Depends(get_recognition_router),
):
    """Загрузить новую запись распознавания."""
    return await router_instance.save_recognition(data)


@router.delete("/delete/{record_id}", response_model=RecognitionResponse)
async def delete_recognition(
    record_id: str,
    router_instance: RecognitionRouter = Depends(get_recognition_router),
):
    """Удалить запись распознавания по ID."""
    return await router_instance.delete_recognition(record_id)


@router.get("/all")
async def get_all_recognition(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: Optional[int] = Query(None, ge=1, description="Максимальное количество записей"),
    router_instance: RecognitionRouter = Depends(get_recognition_router),
):
    """Получить все записи распознавания с пагинацией."""
    return await router_instance.get_all_recognition(skip=skip, limit=limit)


@router.get("/get_by_user_id")
async def get_recognition_by_user(
    user_id: Optional[int],
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: Optional[int] = Query(None, ge=1, description="Максимальное количество записей"),
    router_instance: RecognitionRouter = Depends(get_recognition_router),
):
    """Получить все записи распознавания для пользователя с пагинацией."""
    return await router_instance.get_recognition_by_user_id(
        user_id, skip=skip, limit=limit,
    )


@router.get("/get_by_product_id/{product_id}")
async def get_recognition_by_product(
    product_id: int,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: Optional[int] = Query(None, ge=1, description="Максимальное количество записей"),
    router_instance: RecognitionRouter = Depends(get_recognition_router),
):
    """Получить все записи распознавания для продукта с пагинацией."""
    return await router_instance.get_recognition_by_product_id(
        product_id, skip=skip, limit=limit,
    )


@router.get("/get_by_id/{record_id}")
async def get_recognition_by_id(
    record_id: str,
    router_instance: RecognitionRouter = Depends(get_recognition_router),
):
    """Получить запись распознавания по ID."""
    return await router_instance.get_recognition_by_id(record_id)
