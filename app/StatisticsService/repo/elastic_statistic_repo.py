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

    