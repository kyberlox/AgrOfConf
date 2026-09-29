"""OpenTelemetry: провайдер трейсов + авто-инструментация.

Трейсы уходят по OTLP в OpenTelemetry Collector (tail-sampling),
оттуда — в Tempo. UI — Grafana (datasource Tempo).
"""
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

OTEL_ENDPOINT = os.getenv(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces"
)
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "agrof-conf-api")
OTEL_SERVICE_VERSION = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")

# Эндпоинты, которые не инструментируем (служебные / пробные)
EXCLUDED_URLS = "/metrics,/health,/api/docs,/api/openapi.json"


def setup_tracing(app, sqlalchemy_engines=None):
    """Настраивает TracerProvider, авто-инструментацию и возвращает tracer.

    sqlalchemy_engines: список уже созданных engine (SQLAlchemyInstrumentor
    перехватывает только те движки, которые созданы ПОСЛЕ вызова instrument()).
    """
    provider = TracerProvider(
        resource=Resource.create(
            {
                SERVICE_NAME: OTEL_SERVICE_NAME,
                SERVICE_VERSION: OTEL_SERVICE_VERSION,
                "deployment.environment": os.getenv("ENV", "dev"),
            }
        )
    )
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT))
    )
    trace.set_tracer_provider(provider)

    # FastAPI — корень каждой трассы (HTTP-запрос)
    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=provider, excluded_urls=EXCLUDED_URLS
    )

    # Внешние HTTP-вызовы (GigaChat, внутренние API)
    try:
        HTTPXClientInstrumentor().instrument()
    except Exception:
        pass  # httpx может отсутствовать в рантайме

    # Redis (сессии, кэш) — перехват объектов, созданных после instrument()
    try:
        RedisInstrumentor().instrument()
    except Exception:
        pass

    # SQLAlchemy: инструментируем явно переданные движки (создаются при импорте БД)
    if sqlalchemy_engines:
        for engine in sqlalchemy_engines:
            if engine is None:
                continue
            # AsyncEngine не поддерживает события напрямую (OTel бросает
            # NotImplementedError) — инструментируем его sync_engine.
            target = getattr(engine, "sync_engine", engine)
            try:
                SQLAlchemyInstrumentor().instrument(engine=target)
            except Exception as e:
                print(f"⚠️ Не удалось инструментировать SQLAlchemy: {e}")

    return trace.get_tracer("agrof.business")


def add_user_id_to_span(user_id):
    """Кладёт user.id в текущий span (вызывается из session_middleware)."""
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("user.id", str(user_id))