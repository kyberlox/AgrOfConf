import asyncio
from typing import Optional, Union, Dict, Any, List
from elasticsearch import NotFoundError
from fastapi import HTTPException
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

    async def update_status(self, id: Union[str, int], status: str) -> dict:
        """
        Обновляет поле status у документа по его _id.
        Использует Elasticsearch _update API (partial update).
        """
        try:
            response = await asyncio.to_thread(
                self.db.update,
                index=self.model,
                id=str(id),
                body={"doc": {"status": status}},
            )
            data = {
                "index": response.get("_index"),
                "id": response.get("_id"),
                "result": response.get("result"),
                "version": response.get("_version"),
            }
            print(response, 'Че приходит')
            return {"success": True, "elastic_response": data}
        except NotFoundError:
            raise HTTPException(status_code=404, detail="Document not found")
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_all(
        self,
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        ko_users: Optional[List[int]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> list:
        filter_keys = []
        if user_id:
            filter_keys.append({"term": {"user_id": user_id}})
        if product_id:
            filter_keys.append({"term": {"product_id": product_id}})
        if status:
            filter_keys.append({"term": {"status": status}})
        if ko_users:
            filter_keys.append({"terms": {"user_id": ko_users}})

        date_range = {}
        if date_from is not None:
            date_range["gte"] = date_from + " 00:00:00"
        
        if not date_to:
            date_range["lte"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        else:
            date_range["lte"] = date_to + " 00:00:00"
        filter_keys.append({"range": {"date_search": date_range}})

        if filter_keys:
            body: dict = {
                "query": {"bool": {"must": {"match_all": {}}, "filter": filter_keys}},
                "sort": [{"date_search": {"order": "desc"}}]
            }
        else:
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

    async def last_document_number(self, user_id: int) -> int:
        """
        Возвращает порядковый номер документа указанного пользователя.
        Сортировка по date_search desc, берётся только последняя запись.
        Если записей нет — возвращает 0.
        """
        body: dict = {
            "query": {"term": {"user_id": user_id}},
            "sort": [{"date_search": {"order": "desc"}}],
            "size": 1
        }
        try:
            response = await asyncio.to_thread(
                self.db.search, index=self.model, body=body
            )
            if response["hits"]["total"]["value"] == 0:
                return 0
            last_doc = response["hits"]["hits"][0]["_source"]
            return last_doc.get("document_number", 0)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_by_key_and_value(
        self,
        key: str,
        value: Union[str, int, float],
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        ko_users: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> list:
        """Поиск по ключу и значению."""
        filter_keys = []
        if user_id:
            filter_keys.append({"term": {"user_id": user_id}})
        if product_id:
            filter_keys.append({"term": {"product_id": product_id}})
        if status:
            filter_keys.append({"term": {"status": status}})
        if ko_users:
            filter_keys.append({"terms": {"user_id": ko_users}})

        date_to = date_to or datetime.now()
        date_range = {}
        if date_from is not None:
            date_range["gte"] = date_from.strftime("%d.%m.%Y %H:%M:%S")
        date_range["lte"] = date_to.strftime("%d.%m.%Y %H:%M:%S")
        filter_keys.append({"range": {"date_search": date_range}})

        if filter_keys:
            body: dict = {
                "query": {"bool": {"must": {"match": {key: value}}, "filter": filter_keys}},
                "sort": [{"date_search": {"order": "desc"}}]
            }
        else:
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
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        ko_users: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
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

        # --- Фильтры (опциональные параметры) ---
        filter_conditions = []
        if user_id is not None:
            filter_conditions.append({"term": {"user_id": user_id}})
        if product_id is not None:
            filter_conditions.append({"term": {"product_id": product_id}})
        if status is not None:
            filter_conditions.append({"term": {"status": status}})
        if ko_users:
            filter_conditions.append({"terms": {"user_id": ko_users}})

        date_to = date_to or datetime.now()
        date_range = {}
        if date_from is not None:
            date_range["gte"] = date_from.strftime("%d.%m.%Y %H:%M:%S")
        date_range["lte"] = date_to.strftime("%d.%m.%Y %H:%M:%S")
        filter_conditions.append({"range": {"date_search": date_range}})

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
            bool_query = {"must": must_conditions}
            if filter_conditions:
                bool_query["filter"] = filter_conditions
            query = {"bool": bool_query}
        else:
            # Для строк: multi_match по текстовым полям + query_string по keyword
            bool_query = {
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
            if filter_conditions:
                bool_query["filter"] = filter_conditions
            query = {"bool": bool_query}

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

    async def get_statistics(
        self,
        user_id: Optional[int] = None,
        ko_users: Optional[List[int]] = None,
    ) -> dict:
        """
        Возвращает статистику по документам:
          - за текущий месяц (+ разница с прошлым месяцем)
          - за текущий день (+ разница с прошлым днём)
          - за текущий год (+ разница с прошлым годом)
          - за всё время

        Аргументы:
            user_id: фильтр по одному пользователю.
            ko_users: фильтр по списку пользователей.

        Возвращает словарь:
            {
                "month": {"current": int, "previous": int, "diff": int},
                "day":   {"current": int, "previous": int, "diff": int},
                "year":  {"current": int, "previous": int, "diff": int},
                "total": int,
            }
        """
        now = datetime.now()

        # --- Общий фильтр по пользователям ---
        user_filter = []
        if user_id is not None:
            user_filter.append({"term": {"user_id": user_id}})
        if ko_users:
            user_filter.append({"terms": {"user_id": ko_users}})

        def _build_count_body(
            gte: Optional[str] = None,
            lte: Optional[str] = None,
        ) -> dict:
            """Собрать body для _count с фильтром по дате и пользователям."""
            filters = []
            if gte is not None or lte is not None:
                range_clause = {}
                if gte is not None:
                    range_clause["gte"] = gte
                if lte is not None:
                    range_clause["lte"] = lte
                filters.append({"range": {"date_search": range_clause}})
            filters.extend(user_filter)

            if filters:
                return {"query": {"bool": {"filter": filters}}}
            return {"query": {"match_all": {}}}

        def _format_date(dt: datetime) -> str:
            return dt.strftime("%d.%m.%Y %H:%M:%S")

        try:
            # --- Месяц ---
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            prev_month_start = (month_start - relativedelta(months=1)).replace(day=1)
            prev_month_end = month_start - timedelta(seconds=1)

            month_current = await asyncio.to_thread(
                self.db.count,
                index=self.model,
                body=_build_count_body(
                    gte=_format_date(month_start),
                    lte=_format_date(now),
                ),
            )
            month_previous = await asyncio.to_thread(
                self.db.count,
                index=self.model,
                body=_build_count_body(
                    gte=_format_date(prev_month_start),
                    lte=_format_date(prev_month_end),
                ),
            )

            # --- День ---
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            prev_day_start = day_start - timedelta(days=1)
            prev_day_end = day_start - timedelta(seconds=1)

            day_current = await asyncio.to_thread(
                self.db.count,
                index=self.model,
                body=_build_count_body(
                    gte=_format_date(day_start),
                    lte=_format_date(now),
                ),
            )
            day_previous = await asyncio.to_thread(
                self.db.count,
                index=self.model,
                body=_build_count_body(
                    gte=_format_date(prev_day_start),
                    lte=_format_date(prev_day_end),
                ),
            )

            # --- Год ---
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            prev_year_start = year_start.replace(year=year_start.year - 1)
            prev_year_end = year_start - timedelta(seconds=1)

            year_current = await asyncio.to_thread(
                self.db.count,
                index=self.model,
                body=_build_count_body(
                    gte=_format_date(year_start),
                    lte=_format_date(now),
                ),
            )
            year_previous = await asyncio.to_thread(
                self.db.count,
                index=self.model,
                body=_build_count_body(
                    gte=_format_date(prev_year_start),
                    lte=_format_date(prev_year_end),
                ),
            )

            # --- Всё время ---
            total = await asyncio.to_thread(
                self.db.count,
                index=self.model,
                body=_build_count_body(),
            )

            def _get_count(response) -> int:
                return response.get("count", 0)

            mc = _get_count(month_current)
            mp = _get_count(month_previous)
            dc = _get_count(day_current)
            dp = _get_count(day_previous)
            yc = _get_count(year_current)
            yp = _get_count(year_previous)
            tc = _get_count(total)

            return {
                "month": {"current": mc, "previous": mp, "diff": mc - mp},
                "day":   {"current": dc, "previous": dp, "diff": dc - dp},
                "year":  {"current": yc, "previous": yp, "diff": yc - yp},
                "total": tc,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}