# Observability Plan — AgrOfConf

## 1. Цель

Дать проекту полную наблюдаемость по трём сигналам:

| Сигнал | Инструмент | UI | Хранилище |
|---|---|---|---|
| Метрики | Prometheus + прометей-клиент в FastAPI | Grafana | TSDB Prometheus |
| Трейсы | OpenTelemetry SDK + OTel Collector | Grafana (Tempo) | Tempo |
| Логи | JSON-логи + async bulk-хэндлер (вариант B2) | Grafana (Elasticsearch data source) | Elasticsearch 9.1 (уже развёрнут) |

**Kibana отключается/удаляется** — логи из Elasticsearch смотрим через Grafana.

Единая точка входа — **Grafana на :3000**: метрики, трассы (Tempo) и логи (ES) в одном окне, связка по общему `trace_id`.

Все новые модули и конфиги размещаются в **`app/Observability/`**, а сервисы наблюдаемости добавляются в **`docker-compose.yaml`** (боевой compose), НЕ в `docker-compose.dev.yaml`.

```mermaid
flowchart LR
  subgraph Docker["docker-compose.yaml (app-network)"]
    API[fastapi :8000]
    API -.OTLP трассы.:-> COL[otel-collector :4317/4318]
    COL --> TEMPO[tempo :3200]
    API -.метрики /metrics.:-> PROM[prometheus :9090]
    NE[node-exporter :9100] --> PROM
    API -.bulk JSON логи.:-> ES[(elasticsearch :9200)]
    PROM --> GRAF[grafana :3000]
    TEMPO --> GRAF
    ES --> GRAF
  end
  NE -- CPU, RAM, диск, сеть, load --> PROM
```

---

## 2. Структура папки `app/Observability/`

```
app/Observability/
├── __init__.py                     # пустой, чтобы модуль импортировался как app.Observability
├── tracing.py                      # OTel: провайдер + авто-инструментация + setup_tracing(app)
├── logging_config.py               # JSON-логгер + ElasticBulkHandler (доставка логов в ES, B2)
├── prometheus/
│   └── prometheus.yml              # конфиг Prometheus (scrape fastapi, node-exporter)
├── otel/
│   └── config.yaml                 # OTel Collector: OTLP-приёмник + tail-sampling + batch
├── tempo/
│   └── tempo.yaml                  # конфиг Tempo: OTLP-приёмники, локальное хранилище
└── grafana/
    ├── provisioning/
    │   └── datasources/
    │       └── datasources.yml     # Prometheus, Tempo, Elasticsearch (с cross-линками)
    └── dashboards/
        └── api-overview.json       # дашборды (RPS, latency, ошибки, логи)
```

Пути для volume-mount'ов в compose считаются от корня репозитория: `./app/Observability/...`.

---

## 3. Инструменты и зачем

### 3.1. Prometheus + `prometheus-fastapi-instrumentator` — метрики
- **Зачем:** метрики производительности и надёжности API: RPS, latency (p50/p95/p99), error rate.
- **Как:** библиотека автоматически отдаёт стандартный набор HTTP-метрик на `/metrics`; Prometheus опрашивает (scrape) каждые 15s.
- **Почему:** стандарт для метрик; дешёвый по ресурсам; у Grafana нативный datasource.

### 3.2. Node Exporter — метрики хоста (вопрос №2)
- **Что:** демон Prometheus, читающий системную статистику Linux (`/proc`, `/sys`) и отдающий её на :9100.
- **Метрики:** CPU (загрузка, iowait), память (used/free, swap), диск (свободное место, IOPS, latency), сеть (RX/TX, ошибки), load average, uptime, файловые дескрипторы.
- **Зачем:** видеть, что железо не узкое место (память из-за ES Xms/Xmx 1g) и диски не переполняются (важно для retention логов).

### 3.3. Grafana — единый UI (вместо Kibana)
- **Зачем:** один интерфейс для метрик (Prometheus), трасс (Tempo) и логов (Elasticsearch) + алерты + дашборды.
- **Как:** авто-провижининг datasource'ов через provisioning-файлы; дашборды — JSON в репозитории.
- **Почему вместо Kibana:** Kibana — третий лишний UI; Grafana уже нужна для метрик и трасс, а логи из ES показывает через официальный `elasticsearch` data source с `@timestamp` в качестве time field.

### 3.4. OpenTelemetry SDK + Collector + Tempo — трассы
- **Зачем:** видеть полный путь каждого запроса: сессия Redis → SQL → pandas-поиск → OCR/GigaChat → рендер ТКП, с таймингами.
- **Как:** OTel SDK в FastAPI автоматически инструментирует FastAPI, SQLAlchemy, httpx, redis; спаны по OTLP уходят в Collector (tail-sampling + batch), затем в Tempo.
- **Почему OTel:** открытый стандарт, автоматическая корреляция с логами через `trace_id`.
- **Почему Tempo:** нативный бэкенд трасс для Grafana (Explore), отдельное лёгкое хранилище, дружит с tail-sampling.

### 3.5. Elasticsearch + async bulk-хэндлер (вариант B2) — логи
- **Зачем:** логи FastAPI попадают в уже развёрнутый ES и отображаются в Grafana.
- **Как (B2):** в [`app/Observability/logging_config.py`](app/Observability/logging_config.py:1) — собственный async `ElasticBulkHandler`, который копит записи и bulk-индексирует их в ES напрямую (клиент `AsyncElasticsearch`, хост из env). Никаких Filebeat/Logstash.
- **Почему B2:** логи нужны только от FastAPI; одним сервисом меньше; доставка не зависит от файлов/ротаций; сразу структурный JSON с `trace_id`.
- **TTL:** ILM-политика `app-logs-ttl` удаляет документы через 30 дней после записи.

---

## 4. Метрики — детали

### 4.1. Пакеты
Добавить в [`app/requirements.txt`](app/requirements.txt:1):
```
prometheus-fastapi-instrumentator>=7.0.0
prometheus-client
```

### 4.2. Подключение в [`app/main.py`](app/main.py:52)
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator(
    should_group_status_codes=True,
    should_group_untemplated=True,
    excluded_handlers=["/metrics", "/health", "/api/docs", "/api/openapi.json"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
```
В [`app/main.py`](app/main.py:73) список `open_links` дополнить `"/metrics"` и `"/health"`, иначе middleware авторизации вернёт 401 на пробы.

### 4.3. Бизнес-метрики (опционально)
`Counter`/`Histogram` для подборов, распознаваний, ТКП. В лейблы — только `user_id` и подобное, **без PII**.

### 4.4. Конфиг `app/Observability/prometheus/prometheus.yml`
```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: prometheus
    static_configs: [{ targets: ["prometheus:9090"] }]
  - job_name: fastapi
    metrics_path: /metrics
    static_configs: [{ targets: ["fastapi:8000"] }]
  - job_name: node
    static_configs: [{ targets: ["node-exporter:9100"] }]
```
Внутри сети `app-network` Prometheus обращается к `fastapi:8000` напрямую.

---

## 5. Трейсы — детали

### 5.1. Пакеты
```
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-http
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-sqlalchemy
opentelemetry-instrumentation-httpx
opentelemetry-instrumentation-redis
```

### 5.2. Модуль `app/Observability/tracing.py`
```python
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces")

def setup_tracing(app):
    provider = TracerProvider(resource=Resource.create({
        SERVICE_NAME: "agrof-conf-api",
        SERVICE_VERSION: "1.0.0",
        "deployment.environment": os.getenv("ENV", "dev"),
    }))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT)))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=provider,
        excluded_urls="/metrics,/health,/api/docs,/api/openapi.json",
    )
    SQLAlchemyInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    return trace.get_tracer(__name__)
```

Подключение в [`app/main.py`](app/main.py:52):
```python
from .Observability.tracing import setup_tracing
setup_tracing(app)
```
В `session_middleware` после получения `user_id` — добавить в текущий span атрибут `user.id`.

### 5.3. Конфиг `app/Observability/otel/config.yaml` — tail-sampling (100% ошибок, все медленные >1s, 10% остальных) + batch
```yaml
receivers:
  otlp:
    protocols: { grpc: {}, http: {} }
processors:
  tail_sampling:
    decision_wait: 30s
    policies:
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow
        type: latency
        latency: { threshold_ms: 1000 }
      - name: sample-10
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }
  batch:
exporters:
  otlp:
    endpoint: tempo:4317
    tls: { insecure: true }
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [tail_sampling, batch]
      exporters: [otlp]
```

### 5.4. Конфиг `app/Observability/tempo/tempo.yaml`
```yaml
server:
  http_listen_port: 3200
distributor:
  receivers:
    otlp:
      protocols:
        grpc: { endpoint: 0.0.0.0:4317 }
        http: { endpoint: 0.0.0.0:4318 }
storage:
  trace:
    backend: local
    wal: { path: /var/tempo/wal }
    local: { path: /var/tempo/traces }
```

### 5.5. Правила оформления трасс (как «грамотно»)
1. Корень трассы — HTTP-запрос (автоматически от FastAPI-инструментации).
2. Спан = атомарная операция: SQL, Redis, внешний HTTP, тяжёлая CPU-операция. Не оборачивать каждую строчку.
3. Семантические атрибуты: `db.system`, `http.method`, `http.route`, `http.status_code` — стандарты OTel; свои: `user.id`, `request.id`, `product.id`, `tkp.id`.
4. **Без PII** в атрибутах: никаких ФИО, email, тел документов, содержимого файлов.
5. Ошибки: `span.record_exception(exc)` + статус ERROR.
6. Имена спанов по шаблону `действие.ресурс`: `ocr.process`, `tkp.render`, `module_search.pandas`, `gigachat.completion`, `auth.session_check`.
7. Самплинг — на стороне Collector (tail-sampling), не в SDK.
8. Корреляция с логами: каждый лог несёт `trace_id`/`span_id`.

Ручные спаны для тяжёлых операций (пример):
```python
from opentelemetry import trace
tracer = trace.get_tracer("agrof.business")
with tracer.start_as_current_span("ocr.process") as span:
    result = run_ocr(...)
    span.set_attribute("ocr.pages", pages)
```

---

## 6. Логи — детали (вариант B2)

### 6.1. Структура данных
Логи НЕ идут в бизнес-индексы [`selection_index`/`recognition_index`](app/StatisticsService/set/settings.py:1) — там статистика без TTL. Отдельное пространство:
- **Data stream:** `logs-agrof.app-default` → физические индексы `logs-agrof.app-default-000001` и т.д. (rollover автоматический).
- **ILM-политика `app-logs-ttl`:** hot (rollover 1gb/7d) → delete через **30 дней** (`min_age: 30d`).

### 6.2. ILM-политика (TTL 30 дней)
```bash
curl -X PUT "http://elasticsearch:9200/_ilm/policy/app-logs-ttl" -H 'Content-Type: application/json' -d '{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": { "rollover": { "max_size": "1gb", "max_age": "7d" } }
      },
      "delete": {
        "min_age": "30d",
        "actions": { "delete": {} }
      }
    }
  }
}'
```
`min_age: 30d` — и есть TTL: документы удаляются через 30 дней после записи. Меняется одним параметром.

### 6.3. Index template + data stream
```bash
curl -X PUT "http://elasticsearch:9200/_index_template/logs-agrof" -H 'Content-Type: application/json' -d '{
  "index_patterns": ["logs-agrof.*"],
  "data_stream": {},
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "index.lifecycle.name": "app-logs-ttl"
    },
    "mappings": {
      "properties": {
        "@timestamp":   { "type": "date" },
        "message":      { "type": "text" },
        "level":        { "type": "keyword" },
        "logger":       { "type": "keyword" },
        "service.name": { "type": "keyword" },
        "trace_id":     { "type": "keyword" },
        "span_id":      { "type": "keyword" },
        "user_id":      { "type": "keyword" },
        "http": {
          "properties": {
            "method":      { "type": "keyword" },
            "route":       { "type": "keyword" },
            "status_code": { "type": "integer" },
            "duration_ms": { "type": "float" }
          }
        }
      }
    }
  }
}'
```
Первая запись через bulk создаст data stream автоматически. (Шаблон и политику можно оформить функцией в стиле [`el_indexes.py`](app/StatisticsService/model/el_indexes.py:146), например `create_log_index()` в `app/Observability/es_setup.py`.)

### 6.4. Модуль `app/Observability/logging_config.py` — JSON-логирование + bulk-хэндлер (B2)
**Пакет:** `python-json-logger>=3.2.1` в [`app/requirements.txt`](app/requirements.txt:1).

```python
import logging
import logging.handlers
import os
import asyncio
from pythonjsonlogger import jsonlogger
from elasticsearch import AsyncElasticsearch
from opentelemetry import trace

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
LOG_DATA_STREAM = os.getenv("LOG_DATA_STREAM", "logs-agrof.app-default")


class OtelJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["@timestamp"] = log_record.get("timestamp") or int(record.created * 1000)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        ctx = trace.get_current_span().get_span_context()
        if ctx.is_valid:
            log_record["trace_id"] = format(ctx.trace_id, "032x")
            log_record["span_id"] = format(ctx.span_id, "016x")


class ElasticBulkHandler(logging.Handler):
    """Async bulk-хэндлер: копит записи и шлёт в ES пачками."""

    def __init__(self, flush_interval=5):
        super().__init__()
        self.flush_interval = flush_interval
        self._client = None
        self._buffer = []
        self._lock = asyncio.Lock()
        self._task = None

    def emit(self, record):
        try:
            self._buffer.append(record.__dict__)
        except Exception:
            self.handleError(record)

    async def start(self):
        if self._client is None:
            self._client = AsyncElasticsearch(
                hosts=[ES_HOST], verify_certs=False
            )
        self._task = asyncio.create_task(self._flush_loop())

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush()

    async def flush(self):
        async with self._lock:
            if not self._buffer:
                return
            docs, self._buffer = self._buffer, []
        if self._client is not None:
            try:
                await self._client.bulk(operations=docs, index=LOG_DATA_STREAM)
            except Exception:
                pass


def setup_logging():
    formatter = OtelJsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    es_handler = ElasticBulkHandler()

    console_handler = logging.StreamHandler()   # docker logs
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(es_handler)
    root.addHandler(console_handler)
    return es_handler
```

Примечания к реализации:
- `setup_logging()` вызывается при импорте (вместо старого [`app/logging_config.py`](app/logging_config.py:1)) либо в startup; возвращённый `es_handler` запускается в `startup_event` через `await es_handler.start()` (рядом с `ensure_elastic_ready()` в [`app/main.py`](app/main.py:198)).
- В `emit` записывается `record.__dict__` (все атрибуты LogRecord + JSON-поля). При желании — фильтровать по уровню/полям перед отправкой.
- Ретраи при недоступности ES — встроены в `AsyncElasticsearch`; при падении ES логи не роняют приложение.
- Старый `RotatingFileHandler` удаляется: источник истины — ES (файл-логи в `./app_logs/fastapi` можно перестать монтировать).

### 6.5. Без Kibana: логи в Grafana
- Из `docker-compose.yaml` убрать сервис `kibana` (если есть) и переменную `KIBANA_TOKEN` из `.env`.
- Grafana data source `Elasticsearch` → `url: http://elasticsearch:9200`, `database: logs-agrof.*`, `timeField: @timestamp`, `esVersion: "9.0.0"`.
- Панели логов: в дашбордах — Logs-панель, в Explore — режим Logs по этому datasource.

---

## 7. Grafana — детали

### 7.1. Конфиг `app/Observability/grafana/provisioning/datasources/datasources.yml`
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: Tempo
    uid: tempo-ds-uid
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      httpMethod: GET
      tracesToLogs:                       # трасса → логи по trace_id
        datasourceUid: elastic-ds-uid
        tags: ["trace_id"]
  - name: Elasticsearch
    uid: elastic-ds-uid
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    database: logs-agrof.*
    jsonData:
      timeField: "@timestamp"
      esVersion: "9.0.0"
      derivedFields:                      # лог → трасса по trace_id
        - name: trace_id
          matcherRegex: '"trace_id":"([a-f0-9]{32})"'
          url: "$${__value.raw}"
          datasourceUid: tempo-ds-uid
```
Cross-линки:
- `derivedFields` в ES-datasource → из любого лога открывается трасса в Tempo.
- `tracesToLogs` в Tempo-datasource → из любого спана открываются логи по `trace_id`.

### 7.2. Дашборды (JSON в `app/Observability/grafana/dashboards/`)
- **API Overview:** RPS, p50/p95/p99 (`http_request_duration_seconds`), error rate по route, статусы 4xx/5xx.
- **Host/Container:** CPU, RAM, диск (от node-exporter).
- **Logs Dashboard:** Logs-панель по `logs-agrof.*` с фильтром по `level`, `http.route`, `user_id`.
- **Алерты (примеры):** error rate > 5% за 5 мин; p95 > 2 s; количество `level=ERROR` в логах за минуту; свободное место на диске < 20%.

---

## 8. Блоки сервисов для `docker-compose.yaml`

> ВНИМАНИЕ: `docker-compose.yaml` находится в списке игнорируемых файлов проекта (`.codeassistantignore`) — файл не читается и не редактируется инструментами. Ниже — готовые блоки, которые нужно **добавить в существующий `docker-compose.yaml`** вручную (или вставить через Code-режим после снятия ограничения). Обязательно проверить совпадение имени сети (`app-network`) с уже объявленной в compose.

Все конфиги монтируются из **`./app/Observability/...`**:

```yaml
  prometheus:
    image: prom/prometheus:v3.4.1
    container_name: prometheus
    volumes:
      - ./app/Observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=30d
    ports:
      - "127.0.0.1:9090:9090"
    networks:
      - app-network

  node-exporter:
    image: prom/node-exporter:v1.9.1
    container_name: node-exporter
    ports:
      - "127.0.0.1:9100:9100"
    networks:
      - app-network

  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.161.0
    container_name: otel-collector
    command: ["--config=/etc/otel/config.yaml"]
    volumes:
      - ./app/Observability/otel/config.yaml:/etc/otel/config.yaml
    ports:
      - "127.0.0.1:4317:4317"
      - "127.0.0.1:4318:4318"
    depends_on:
      - tempo
    networks:
      - app-network

  tempo:
    image: grafana/tempo:2.7.1
    container_name: tempo
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./app/Observability/tempo/tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo
    ports:
      # - "127.0.0.1:4317:4317"
      # - "127.0.0.1:4318:4318"
      - "127.0.0.1:3200:3200"
    networks:
      - app-network

  grafana:
    image: grafana/grafana:11.6.0
    container_name: grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${pswd}
    volumes:
      - ./app/Observability/grafana/provisioning:/etc/grafana/provisioning
      - ./app/Observability/grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-data:/var/lib/grafana
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      - prometheus
      - tempo
    networks:
      - app-network
```

Дополнительно в `docker-compose.yaml`:
- В сервис `fastapi` добавить env: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces` (или вынести в `.env`), `ES_HOST=http://elasticsearch:9200`, `LOG_DATA_STREAM=logs-agrof.app-default`. Также `depends_on: [prometheus, otel-collector]` (опционально).
- В секцию `volumes:` добавить: `prometheus-data:`, `tempo-data:`, `grafana-data:`.
- Убедиться, что сеть `app-network` объявлена и к ней подключены `elasticsearch` и `fastapi`.

---

## 9. Чек-лист внедрения

1. **[app/requirements.txt](app/requirements.txt:1):** + `prometheus-fastapi-instrumentator`, `prometheus-client`, `opentelemetry-*`, `python-json-logger`.
2. **Создать `app/Observability/`:** `__init__.py`, `tracing.py`, `logging_config.py`, `prometheus/prometheus.yml`, `otel/config.yaml`, `tempo/tempo.yaml`, `grafana/provisioning/datasources/datasources.yml`, `grafana/dashboards/`.
3. **[app/main.py](app/main.py:52):** `Instrumentator` + `/metrics`; добавить `/metrics`, `/health` в `open_links`; `setup_tracing(app)`; в startup — `await es_handler.start()` (логи) и создание ES-шаблона/ILM.
4. **Elasticsearch:** ILM-политика `app-logs-ttl` (30d) + index template `logs-agrof` (через curl или функцию в `app/Observability/es_setup.py`).
5. **`docker-compose.yaml`:** добавить блоки из раздела 8 (prometheus, node-exporter, otel-collector, tempo, grafana), убрать kibana, добавить env/volumes/network.
6. **Проверка:** `/metrics` отдаёт метрики; `GET _ilm/policy/app-logs-ttl` — политика есть; первая запись в логах создала data stream `logs-agrof.app-default`; в Grafana Explore — трасса от `trace_id` из лога.

---

## 10. Продакшн-нюансы

- `docker-compose.yaml` — боевой compose; сервисы наблюдаемости добавляются туда (раздел 8). В `docker-compose.dev.yaml` изменения не вносятся (при желании — дублировать для локальной разработки).
- Все порты — только на `127.0.0.1` (кроме публичных nginx/grafana при необходимости), Grafana за basic-auth.
- Retention: Prometheus `--storage.tsdb.retention.time` (30d), Tempo `storage.trace` (default_retention), ILM для логов (30d).
- При включении security в ES — передать креды в bulk-хэндлер через env (`ES_USER`/`ES_PASSWORD`).
- `OTEL_EXPORTER_OTLP_ENDPOINT`, `ES_HOST`, `LOG_DATA_STREAM` — вынести в `.env`.