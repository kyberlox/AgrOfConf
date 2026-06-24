"""
Собственное подключение к БД для StatisticsService.

По умолчанию используется Elasticsearch.
При смене хранилища достаточно заменить реализацию в этой файле —
все роутеры StatisticsService будут использовать новый клиент автоматически.
"""

from ..model.el_connect import elastic_client


def get_statistic_db():
    """
    Возвращает клиент БД для StatisticsService.

    Текущая реализация: Elasticsearch.
    При переходе на PostgreSQL/Mongo достаточно заменить тело функции,
    например:
        from app.TablePakage.model.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            yield session
    """
    return elastic_client