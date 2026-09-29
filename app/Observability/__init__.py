"""
Наблюдаемость AgrOfConf:
- метрики (Prometheus),
- трассы (OpenTelemetry -> OTel Collector -> Tempo),
- логи (JSON + bulk в Elasticsearch, просмотр в Grafana).

Конфиги сопутствующих сервисов лежат рядом:
app/Observability/prometheus, otel, tempo, grafana.
"""