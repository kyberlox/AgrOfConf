"""JSON-логирование + async bulk-хэндлер в Elasticsearch (вариант B2).

Логи от FastAPI bulk-индексируются напрямую в data stream
logs-agrof.app-default (ILM-политика app-logs-ttl, TTL 30 дней).
Просмотр — в Grafana (Elasticsearch datasource), без Kibana.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger
from elasticsearch import AsyncElasticsearch
from opentelemetry import trace

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
ES_USER = os.getenv("ES_USER", "")
ES_PASSWORD = os.getenv("ES_PASSWORD", "")
LOG_DATA_STREAM = os.getenv("LOG_DATA_STREAM", "logs-agrof.app-default")
LOG_FLUSH_INTERVAL = float(os.getenv("LOG_FLUSH_INTERVAL", "5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "agrof-conf-api")


class OtelJsonFormatter(jsonlogger.JsonFormatter):
    """JSON-формат для логов с @timestamp, level и trace_id/span_id."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # ISO8601 UTC c миллисекундами и суффиксом Z — строгий формат для
        # date-поля @timestamp в Elasticsearch / Grafana.
        log_record["@timestamp"] = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["service.name"] = SERVICE_NAME

        ctx = trace.get_current_span().get_span_context()
        if ctx.is_valid:
            log_record["trace_id"] = format(ctx.trace_id, "032x")
            log_record["span_id"] = format(ctx.span_id, "016x")


class ElasticBulkHandler(logging.Handler):
    """Async bulk-хэндлер: копит записи и шлёт их в ES пачками.

    Отправка происходит каждые LOG_FLUSH_INTERVAL секунд (фоновый цикл).
    При недоступности ES запись не роняет приложение — ошибки глотаются.
    """

    def __init__(self, flush_interval: float = LOG_FLUSH_INTERVAL):
        super().__init__()
        self.flush_interval = flush_interval
        self._client = None
        self._buffer = []
        self._lock = asyncio.Lock()
        self._task = None

    def emit(self, record):
        try:
            # Форматируем через OtelJsonFormatter, чтобы в ES уходили итоговые
            # JSON-документы со всеми полями (@timestamp, level, logger,
            # trace_id, span_id), а не сырой record.__dict__.
            self._buffer.append(json.loads(self.format(record)))
        except Exception:
            self.handleError(record)

    def flush(self):
        """Синхронный no-op для совместимости со стандартным logging.

        logging.shutdown() вызывает h.flush() синхронно и не умеет ждать
        корутины (иначе RuntimeWarning: coroutine was never awaited).
        Реальная отправка в ES — в async _flush_es().
        """

    async def start(self):
        """Создаёт AsyncElasticsearch и запускает фоновый flush-цикл."""
        kwargs = {"hosts": [ES_HOST], "verify_certs": False}
        if ES_USER:
            kwargs["basic_auth"] = (ES_USER, ES_PASSWORD)
        self._client = AsyncElasticsearch(**kwargs)
        self._task = asyncio.create_task(self._flush_loop())

    async def stop(self):
        """Отменяет фоновый цикл, отправляет остаток буфера и закрывает клиент."""
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client is not None:
            await self._flush_es()
            await self._client.close()

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush_es()

    async def _flush_es(self):
        """Отправляет накопленный буфер одной bulk-операцией.

        Data stream принимает ТОЛЬКО операции create (op_type=create) —
        обычные index-операции ES отклоняет на уровне каждого документа
        (HTTP при этом всё равно 200, поэтому ошибки нужно читать из тела).
        """
        async with self._lock:
            if not self._buffer:
                return
            docs, self._buffer = self._buffer, []
        if self._client is not None:
            try:
                operations = []
                for doc in docs:
                    operations.append({"create": {"_index": LOG_DATA_STREAM}})
                    operations.append(doc)
                resp = await self._client.bulk(operations=operations)
                if resp.get("errors"):
                    print(
                        f"⚠️ Ошибки bulk в ES: {resp.get('errors')}",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(
                    f"⚠️ Не удалось отправить логи в ES: {e}",
                    file=sys.stderr,
                )


_es_handler: "ElasticBulkHandler | None" = None


def setup_logging() -> ElasticBulkHandler:
    """Настраивает root-логгер: JSON в stdout + bulk-хэндлер в ES.

    Возвращает ElasticBulkHandler, чтобы main запустил его в startup:
        es_handler = setup_logging()
        ...
        await es_handler.start()
    """
    global _es_handler

    formatter = OtelJsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    # Docker logs (stdout) — человекочитаемый JSON
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Bulk-доставка в Elasticsearch
    es_handler = ElasticBulkHandler()
    es_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Приглушаем внутренние служебные логгеры: elasticsearch-py логирует
    # КАЖДЫЙ успешный HTTP-запрос (в т.ч. наш же PUT /_bulk) на уровне INFO —
    # это шум, а не полезные логи. WARNING оставляет видимыми реальные
    # ошибки сети/индексации.
    for noisy in (
        "elastic_transport",
        "elastic_transport.transport",
        "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Не дублируем хэндлеры при повторном вызове (reload/dev)
    for h in list(root.handlers):
        root.removeHandler(h)

    root.addHandler(console_handler)
    root.addHandler(es_handler)

    _es_handler = es_handler
    return es_handler


def get_es_handler() -> "ElasticBulkHandler | None":
    """Возвращает глобальный bulk-хэндлер (если logging уже настроен)."""
    return _es_handler