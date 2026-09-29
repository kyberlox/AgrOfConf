"""Создание ILM-политики и index template для логов в Elasticsearch.

Вызывается в startup_event приложения (после ensure_elastic_ready()).
Идемпотентно: повторные вызовы безопасны.
"""
import os

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from ..StatisticsService.model.el_connect import get_elastic_client

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
LOG_INDEX_PATTERN = os.getenv("LOG_INDEX_PATTERN", "logs-agrof.*")
LOG_DATA_STREAM = os.getenv("LOG_DATA_STREAM", "logs-agrof.app-default")

# TTL логов (delete-фаза ILM)
LOG_RETENTION = os.getenv("LOG_RETENTION", "30d")
# Rollover в hot-фазе
LOG_ROLLOVER_SIZE = os.getenv("LOG_ROLLOVER_SIZE", "1gb")
LOG_ROLLOVER_AGE = os.getenv("LOG_ROLLOVER_AGE", "7d")

ILM_POLICY_NAME = "app-logs-ttl"
INDEX_TEMPLATE_NAME = "logs-agrof"


def _client_or_create():
    """Возвращает рабочий клиент ES (общий из StatisticsService или новый)."""
    client = get_elastic_client()
    if client is not None and client.ping():
        return client
    return Elasticsearch(hosts=[ES_HOST], verify_certs=False)


def create_log_ilm_policy():
    """Создаёт ILM-политику app-logs-ttl (hot rollover + delete через LOG_RETENTION)."""
    es = _client_or_create()
    policy = {
        "policy": {
            "phases": {
                "hot": {
                    "min_age": "0ms",
                    "actions": {
                        "rollover": {
                            "max_size": LOG_ROLLOVER_SIZE,
                            "max_age": LOG_ROLLOVER_AGE,
                        }
                    },
                },
                "delete": {
                    "min_age": LOG_RETENTION,
                    "actions": {"delete": {}},
                },
            }
        }
    }
    # put_lifecycle идемпотентен: перезаписывает политику при необходимости
    es.ilm.put_lifecycle(name=ILM_POLICY_NAME, policy=policy["policy"])
    print(f"✅ ILM-политика {ILM_POLICY_NAME} готова (TTL {LOG_RETENTION})")


def create_log_index_template():
    """Создаёт index template logs-agrof для data stream логов."""
    es = _client_or_create()
    template = {
        "index_patterns": [LOG_INDEX_PATTERN],
        # Приоритет выше системных шаблонов ES (logs@settings/logs@ilm-policy,
        # priority ~100), чтобы применялась наша ILM-политика app-logs-ttl,
        # а не встроенная "logs".
        "priority": 500,
        "data_stream": {},
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": ILM_POLICY_NAME,
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "message": {"type": "text"},
                    "level": {"type": "keyword"},
                    "logger": {"type": "keyword"},
                    "service.name": {"type": "keyword"},
                    "trace_id": {"type": "keyword"},
                    "span_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "http": {
                        "properties": {
                            "method": {"type": "keyword"},
                            "route": {"type": "keyword"},
                            "status_code": {"type": "integer"},
                            "duration_ms": {"type": "float"},
                        }
                    },
                }
            },
        },
    }
    es.indices.put_index_template(name=INDEX_TEMPLATE_NAME, body=template)
    print(f"✅ Index template {INDEX_TEMPLATE_NAME} готов (data stream: {LOG_DATA_STREAM})")


def create_log_setup():
    """Полная подготовка логирования: ILM-политика + index template."""
    try:
        create_log_ilm_policy()
    except Exception as e:
        print(f"⚠️ Не удалось создать ILM-политику: {e}")
    try:
        create_log_index_template()
    except Exception as e:
        print(f"⚠️ Не удалось создать index template: {e}")


def ensure_log_data_stream():
    """Гарантирует существование data stream (создаётся первой bulk-записью)."""
    es = _client_or_create()
    try:
        es.indices.get_data_stream(name=LOG_DATA_STREAM)
        return
    except NotFoundError:
        pass
    except Exception:
        pass
    try:
        es.indices.create_data_stream(name=LOG_DATA_STREAM)
        print(f"✅ Data stream {LOG_DATA_STREAM} создан")
    except Exception as e:
        print(f"⚠️ Не удалось создать data stream: {e}")