from elasticsearch import Elasticsearch

import os
import time
import asyncio

from dotenv import load_dotenv

load_dotenv()

pswd = os.getenv('pswd')


def create_elastic_client(max_retries: int = 2, retry_delay: float = 5):
    """
    Создаёт клиент Elasticsearch.

    Возвращает клиент, если подключение успешно, иначе None.
    Ретраи сокращены — полное ожидание готовности ES выполняет
    `ensure_elastic_ready()` (вызывается при старте приложения).
    """
    for i in range(max_retries):
        try:
            elastic_client = Elasticsearch(
                hosts=["http://elasticsearch:9200"],
                basic_auth=('elastic', pswd),
                verify_certs=False,
                request_timeout=30,
            )

            if elastic_client.ping():
                print("✅ Успешное подключение Elasticsearch!")
                return elastic_client
        except Exception as e:
            print(f"❌ Connection attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(retry_delay)

    return None


# Создаём клиент при импорте. Может быть None, если ES ещё не готов —
# это корректно обрабатывается в ensure_elastic_ready() при старте.
elastic_client = create_elastic_client()


def get_elastic_client():
    """Возвращает текущий (возможно пересозданный) клиент Elasticsearch."""
    return elastic_client


async def ensure_elastic_ready(timeout: float = 600, interval: float = 5):
    """
    Ожидает, пока Elasticsearch станет полностью доступен, пересоздавая клиент
    при необходимости. Используется в startup_event ПЕРЕД созданием индексов,
    чтобы приложение не падало с AttributeError из-за None-клиента.

    Возвращает рабочий клиент. По истечении timeout — бросает RuntimeError.
    """
    global elastic_client

    deadline = time.time() + timeout

    while True:
        client = get_elastic_client()
        try:
            if client is not None and await asyncio.to_thread(client.ping):
                return client
        except Exception:
            pass

        # Пересоздаём клиент и пробуем снова.
        try:
            elastic_client = create_elastic_client(max_retries=1, retry_delay=1)
        except Exception as e:
            print(f"⚠️ Не удалось создать клиент ES: {e}")

        if time.time() >= deadline:
            raise RuntimeError(
                f"Elasticsearch не стал доступен за {timeout} секунд"
            )

        print("⏳ Ожидание готовности Elasticsearch...")
        await asyncio.sleep(interval)