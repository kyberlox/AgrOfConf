import asyncio
from typing import Optional, Union, Dict, Any
from elasticsearch import NotFoundError
from fastapi import HTTPException

from .abstracktion_repo import DatabaseStatistic

def convert_to_responce_format(data: Dict[str, Any]) -> Dict[str, Any]:
    source = data.get("_source", {})

    result = {
        **source,
        "id": data.get("_id"),
    }
    return result

class ElasticStatisticRepo(DatabaseStatistic):
    """Репозиторий для работы с базой данных Elasticsearch. Реализует интерфейс DatabaseStatistic."""

    def __init__(self, model, db):
        super().__init__(model, db)

    async def save(self, data):
        try:
            response = await asyncio.to_thread(
                self.db.index, index=self.model, body=data
            )
            return {"success": True, "elastic_response": response}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete(self, id: Union[str, int]):
        """
        Удаляет документ по его _id.
        """
        try:
            response = await asyncio.to_thread(
                self.db.delete, index=self.model, id=str(id)
            )
            data = {
                "index": response.get("_index"),
                "id": response.get("_id"),
                "result": response.get("result"),
                "version": response.get("_version")
            }
            return {"success": True, "elastic_response": data}
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail="Document not found")
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_all(self, skip: int = 0, limit: Optional[int] = None):
        body: dict = {
            "query": {"match_all": {}},
            "sort": [{"date_search": {"order": "desc"}}]
        }
        if limit is not None:
            body["from"] = skip
            body["size"] = limit
        try:
            response = await asyncio.to_thread(
                self.db.search, index=self.model, body=body
            )
            if response["hits"]["total"]["value"] == 0:
                return []
            result = [convert_to_responce_format(hit) for hit in response["hits"]["hits"]]
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_by_id(self, id: Union[str, int]):
        try:
            response = await asyncio.to_thread(
                self.db.get, index=self.model, id=str(id)
            )
            if response.get("found") is False:

                return []
            return convert_to_responce_format(response)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail="Document not found")
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: Optional[int] = None):
        body: dict = {
            "query": {"term": {"user_id": user_id}},
            "sort": [{"date_search": {"order": "desc"}}]
        }
        if limit is not None:
            body["from"] = skip
            body["size"] = limit
        try:
            response = await asyncio.to_thread(
                self.db.search, index=self.model, body=body
            )
            if response["hits"]["total"]["value"] == 0:
                return []
            result = [convert_to_responce_format(hit) for hit in response["hits"]["hits"]]
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_by_product_id(self, product_id: int, skip: int = 0, limit: Optional[int] = None):
        body: dict = {
            "query": {"term": {"product_id": product_id}},
            "sort": [{"date_search": {"order": "desc"}}]
        }
        if limit is not None:
            body["from"] = skip
            body["size"] = limit
        try:
            response = await asyncio.to_thread(
                self.db.search, index=self.model, body=body
            )
            if response["hits"]["total"]["value"] == 0:
                return []
            result = [convert_to_responce_format(hit) for hit in response["hits"]["hits"]]
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_by_key_and_value(self, key: str, value: str, skip: int = 0, limit: Optional[int] = None) -> list:
        """Поиск по ключу и значению."""
        body: dict = {
            "query": {"match": {key: value}},
            "sort": [{"date_search": {"order": "desc"}}]
        }
        if limit is not None:
            body["from"] = skip
            body["size"] = limit
        try:
            response = await asyncio.to_thread(
                self.db.search, index=self.model, body=body
            )
            if response["hits"]["total"]["value"] == 0:
                return []
            result = [convert_to_responce_format(hit) for hit in response["hits"]["hits"]]
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_all_fields(
        self,
        value: Union[str, int, float],
        skip: int = 0,
        limit: Optional[int] = None,
        highlight_pre_tag: str = "<em>",
        highlight_post_tag: str = "</em>",
    ) -> list:
        """
        Поиск по всем полям документа по переданному значению (строка или число).
        Возвращает документы с подсветкой найденных совпадений.

        Аргументы:
            value: Значение для поиска (строка или число).
            skip: Смещение для пагинации.
            limit: Максимальное количество результатов.
            highlight_pre_tag: Открывающий тег для подсветки.
            highlight_post_tag: Закрывающий тег для подсветки.

        Возвращает список словарей, каждый из которых содержит:
            - все поля исходного документа (_source)
            - "id": _id документа
            - "highlight": словарь с подсвеченными фрагментами по полям
        """
        is_numeric = isinstance(value, (int, float))
        str_value = str(value)

        # --- Базовый запрос: ищем по всем полям ---
        if is_numeric:
            # Для чисел: term-запрос по числовым полям + multi_match по строковым
            # (на случай если число хранится как строка)
            must_conditions = [
                {"multi_match": {
                    "query": str_value,
                    "type": "cross_fields",
                    "fields": [
                        "product_name^3",
                        "product_description",
                        "user_fio^2",
                        "user_email",
                        "user_directorate",
                        "user_work_position",
                        "user_department",
                        "user_work_city",
                        "user_work_phone",
                        "parameters.*_text",
                    ],
                    "operator": "or",
                }},
            ]
            # keyword-поля (включая числовые как keyword)
            must_conditions.append({
                "query_string": {
                    "query": str_value,
                    "fields": [
                        "product_id",
                        "user_id",
                        "product_manufacturer",
                        "user_uuid",
                        "user_email",
                        "user_directorate",
                        "user_work_position",
                        "user_department",
                        "user_work_city",
                        "user_work_phone",
                        "total_coast",
                        "parameters.*",
                    ],
                    "default_operator": "OR",
                }
            })
            # Числовые поля (long/double) — точное совпадение
            must_conditions.append({
                "bool": {
                    "should": [
                        {"term": {"user_office": value}},
                        {"term": {"parameters.long_*": value}},
                    ]
                }
            })
            query = {"bool": {"must": must_conditions}}
        else:
            # Для строк: multi_match по текстовым полям + query_string по keyword
            query = {
                "bool": {
                    "should": [
                        # Текстовые поля с русским анализатором
                        {"multi_match": {
                            "query": str_value,
                            "type": "cross_fields",
                            "fields": [
                                "product_name^3",
                                "product_description",
                                "user_fio^2",
                                "user_email",
                                "user_directorate",
                                "user_work_position",
                                "user_department",
                                "user_work_city",
                                "user_work_phone",
                                "parameters.*_text",
                            ],
                            "operator": "or",
                        }},
                        # keyword-поля (точное совпадение или префикс)
                        {"query_string": {
                            "query": str_value,
                            "fields": [
                                "product_id",
                                "user_id",
                                "product_manufacturer",
                                "user_uuid",
                                "user_email",
                                "user_directorate",
                                "user_work_position",
                                "user_department",
                                "user_work_city",
                                "user_work_phone",
                                "total_coast",
                                "parameters.*",
                            ],
                            "default_operator": "OR",
                        }},
                    ],
                    "minimum_should_match": 1,
                }
            }

        # --- Highlight: подсветка совпадений ---
        highlight = {
            "pre_tags": [highlight_pre_tag],
            "post_tags": [highlight_post_tag],
            "fields": {
                # Текстовые поля — с фрагментами
                "product_name": {
                    "number_of_fragments": 3,
                    "fragment_size": 150,
                },
                "product_description": {
                    "number_of_fragments": 3,
                    "fragment_size": 150,
                },
                "user_fio": {
                    "number_of_fragments": 3,
                    "fragment_size": 150,
                },
                # keyword-поля — подсвечиваем всё значение целиком
                "product_id": {"type": "plain", "number_of_fragments": 0},
                "user_id": {"type": "plain", "number_of_fragments": 0},
                "product_manufacturer": {"type": "plain", "number_of_fragments": 0},
                "user_uuid": {"type": "plain", "number_of_fragments": 0},
                "user_email": {"type": "plain", "number_of_fragments": 0},
                "user_directorate": {"type": "plain", "number_of_fragments": 0},
                "user_work_position": {"type": "plain", "number_of_fragments": 0},
                "user_department": {"type": "plain", "number_of_fragments": 0},
                "user_work_city": {"type": "plain", "number_of_fragments": 0},
                "user_work_phone": {"type": "plain", "number_of_fragments": 0},
                "total_coast": {"type": "plain", "number_of_fragments": 0},
                "user_office": {"type": "plain", "number_of_fragments": 0},
                # Параметры (динамические) — глобально
                "parameters.*": {
                    "number_of_fragments": 3,
                    "fragment_size": 100,
                },
            },
        }

        body: dict = {
            "query": query,
            "highlight": highlight,
            "sort": [{"date_search": {"order": "desc"}}],
        }
        if limit is not None:
            body["from"] = skip
            body["size"] = limit

        try:
            response = await asyncio.to_thread(
                self.db.search, index=self.model, body=body
            )
            if response["hits"]["total"]["value"] == 0:
                return []

            result = []
            for hit in response["hits"]["hits"]:
                doc = convert_to_responce_format(hit)
                # Добавляем highlight в результат, если есть
                if "highlight" in hit:
                    doc["highlight"] = hit["highlight"]
                result.append(doc)

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}