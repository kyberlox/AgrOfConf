# Конфигуратор ПК (SaveOfConf / Agregator)

> Платформа подбора и конфигурирования запорно‑регулирующей арматуры с генерацией ТКП
> (технико‑коммерческого предложения) по продуктам, параметрическим таблицам и чертежам.

Проект состоит из **FastAPI‑бэкенда**, **Vue 3‑фронтенда** и вспомогательной
инфраструктуры (PostgreSQL, Redis, Elasticsearch, Kibana, Nginx), объединяемых через
`docker-compose.yaml`. Система позволяет администратору вести каталог продукции
(«ОЛ» — оборудование), настраивать параметры и таблицы подбора, а инженеру —
пошагово конфигурировать изделие, распознавать опросные листы и формировать ТКП.

---

## Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Структура репозитория](#структура-репозитория)
- [Бэкенд: модули](#бэкенд-модули)
- [Фронтенд](#фронтенд)
- [Запуск](#запуск)
- [Конфигурация (переменные окружения)](#конфигурация)
- [API](#api)
- [Генерация ТКП](#генерация-ткп)
- [Известные проблемы и ограничения](#известные-проблемы-и-ограничения)
- [Разработка](#разработка)

---

## Возможности

- **Каталог продукции** — создание/редактирование товаров, загрузка изображений,
  чертежей и файлов, управление версиями таблиц.
- **Параметризация изделия** — динамические схемы параметров (типы `Table` и `Formula`),
  транслитерация имён, сортировка, видимость по ролям (`field_of_view`).
- **Подбор по таблицам** — последовательный (каскадный) выбор параметров по данным
  Excel‑таблиц, агрегация доступных значений, поиск ошибок подбора.
- **Свободный режим** конфигурирования без обязательной последовательности.
- **Распознавание опросных листов (ОЛ)** — загрузка документов, нейросетевая обработка
  (GigaChat), сравнение распознанных значений с базой.
- **Статистика** — сбор событий распознавания и подборов в Elasticsearch, витрины,
  графики (chart.js) в веб‑интерфейсе.
- **Генерация ТКП** — подстановка данных конфигурации в шаблоны `.docx`/`.xlsx`,
  вставка чертежа, формирование номера документа и сохранение статистики.
- **Авторизация через корпоративный Интранет** — сессии в Redis, синхронизация
  пользователей и ролей.
- **Заявки** — многостадийный жизненный цикл заявок с заказчиками, организациями,
  сроками и процедурами.

---

## Архитектура

```
                    ┌────────────────────────────────────────────────┐
    Браузер         │                 Nginx :80                      │
   (Vue 3 SPA) ────►│  /            → frontend :5173 (Vite preview)  │
                    │  /api/        → fastapi :8000 (FastAPI/Uvicorn)│
                    └────────────────────────────────────────────────┘
                                     │
                     ┌───────────────┼───────────────────────┐
                     ▼               ▼                       ▼
              ┌────────────┐   ┌──────────┐          ┌───────────────┐
              │ PostgreSQL │   │  Redis   │          │ Elasticsearch │
              │ :5432      │   │ :6379    │          │ :9200 / :9300 │
              │ БД app     │   │ сессии   │          │ статистика    │
              └────────────┘   └──────────┘          └───────┬───────┘
                                                             │
                                                     ┌───────▼───────┐
                                                     │    Kibana     │
                                                     │    :5601      │
                                                     └───────────────┘
```

Все сервисы находятся в одной docker‑сети `app-network`. Внутри контейнеров обращения
к инфраструктуре идут по **именам контейнеров**: `postgres`, `redis`, `elasticsearch`
(захардкожены в коде бэкенда, см. [Известные проблемы](#известные-проблемы-и-ограничения)).

---

## Технологический стек

**Бэкенд (`app/`)**
- Python 3.13, FastAPI 0.136, Uvicorn 0.38
- SQLAlchemy 2.0 (async, `asyncpg`), psycopg2
- Redis (`redis`), Elasticsearch 9.1 (`elasticsearch` py‑клиент)
- docxtpl, openpyxl, pypandoc, PyMuPDF, Pillow
- GigaChat SDK (`gigachat`), openai, httpx
- pandas, alembic, python-dotenv

**Фронтенд (`front/`)**
- Vue 3, Vue Router, Pinia
- Vite 7, TypeScript, Tailwind CSS 4
- ag‑grid‑vue3 (таблицы), chart.js (графики)
- vue3-toastify, vue-draggable-plus, beans-ui-kit
- axios

**Инфраструктура**
- Nginx 1.27 (reverse proxy + CORS)
- PostgreSQL 18.1, Redis (alpine), Elasticsearch 9.1, Kibana 9.1

---

## Структура репозитория

```
.
├── docker-compose.yaml          # Оркестрация всех сервисов
├── .env.example                 # Шаблон переменных окружения
├── nginx/default.conf           # Reverse‑proxy: фронт + /api
├── app/                         # Бэкенд FastAPI
│   ├── main.py                  # Точка входа, подключение роутеров
│   ├── logging_config.py        # Логирование (RotatingFileHandler)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── TablePakage/             # Каталог продукции, параметры, ТКП
│   ├── TableSearch/             # Подбор по таблицам, ИИ, распознавание
│   ├── UserService/             # Пользователи, роли, сессии, авторизация
│   ├── StatisticsService/       # Статистика (Elasticsearch/Mongo/Postgres)
│   ├── RequestService/          # Заявки, заказчики, организации
│   └── tempates/                # Шаблоны ТКП (.docx/.xlsx)
└── front/                       # SPA Vue 3
    ├── Dockerfile
    ├── vite.config.ts
    └── src/
        ├── router/index.ts
        ├── stores/              # Pinia: configurator, products, user, ...
        ├── utils/Api.ts         # Axios‑клиент
        └── views/
            ├── homeView/        # Заявки, распознавание, статистика
            ├── configurator/    # Страница конфигуратора (ключевой модуль)
            ├── admin/           # Админка: продукты, параметры
            └── userPage/        # Профиль пользователя
```

---

## Бэкенд: модули

### `TablePakage` — каталог, параметры, таблицы, ТКП

| Файл | Назначение |
|------|-----------|
| `router/products.py` | CRUD продуктов, загрузка изображений (base64/UploadFile) |
| `router/parameters.py` | CRUD схем параметров, создание/переименование колонок таблиц |
| `router/tables.py` | Работа с таблицами продукта |
| `router/parameter_values.py` | Значения параметров |
| `router/tkp_generation.py` | Генерация ТКП из шаблонов docx/xlsx |
| `model/*` | ORM: `Product`, `ParameterSchema`, `DataMartRegistry`, `ProductTable`, `TKP`, файлы и чертежи |

### `TableSearch` — поиск и подбор

| Файл | Назначение |
|------|-----------|
| `router/module_search.py` | Каскадный подбор по таблицам (SQL‑агрегации) |
| `router/module_search_pandas.py` | Подбор на основе pandas |
| `router/AI.py` | Нейросетевое распознавание (GigaChat) |
| `router/blocks.py` | Управление блоками параметров |
| `utils/*` | Конвертация ОЛ, поиск формул, промпты, работа с datamart |

### `formulas` — новая система расчёта формул

| Файл | Назначение |
|------|-----------|
| `algorithms.py` | Библиотека функций расчёта (например `count_A`) |
| `validators.py` | Библиотека функций валидации (например `validate_nonzero`) |
| `engine.py` | Ядро: `FormulaContext`, асинхронный решатель зависимостей |
| `registry.py` | Реестры имён функций (безопасный вызов по имени из БД) |
| `router.py` | Эндпоинт `/api/formula_functions` (список доступных функций) |
| `integration.py` | Интеграция в `module_search` (новые формулы + fallback) |

### `UserService` — пользователи и сессии

| Файл | Назначение |
|------|-----------|
| `router/auth_router.py` | Авторизация через Интранет, создание сессии |
| `router/users_router.py` | CRUD пользователей |
| `router/roots_router.py` | Роли/права |
| `services/redis_service.py` | Хранение сессий в Redis |
| `utils/auth_utils.py` | Проверка сессии, refresh, зависимости `get_user_id_by_session_id` |

### `StatisticsService` — статистика

| Файл | Назначение |
|------|-----------|
| `router/recognition_router.py` | Сбор статистики распознавания |
| `router/selection_router.py` | Сбор статистики подборов, нумерация документов |
| `repo/*` | Абстрактный репозиторий + реализации (Elasticsearch, Mongo, Postgres) |
| `set/settings.py` | Имена индексов: `selection_index`, `recognition_index` |

### `RequestService` — заявки

| Файл | Назначение |
|------|-----------|
| `router/requests.py` | Жизненный цикл заявок, заказчики, организации |
| `model/*` | ORM: `Request`, `Customer`, `ContactPerson` |

---

## Фронтенд

Точка входа — [`front/src/main.ts`](front/src/main.ts). Роутер
[`front/src/router/index.ts`](front/src/router/index.ts) определяет страницы:
`/my_requests`, `/ko_requests`, `/configurator/:id`, `/admin`, `/admin/product/:id`,
`/user/:id`, `/login` (редирект на Интранет).

Ключевой модуль платформы — **страница конфигуратора**
[`front/src/views/configurator/Configurator.vue`](front/src/views/configurator/Configurator.vue)
и её компоненты `EngineParams*`. Здесь инженер последовательно выбирает параметры,
видит доступные значения (обновляются каскадно), чертёж и «Маркировку», а в конце
формирует ТКП.

Состояние хранится в Pinia‑сторах:
- [`stores/configurator.ts`](front/src/stores/configurator.ts) — параметры, статус, маркировка, чертёж, ошибки;
- `stores/products.ts` — список продуктов;
- `stores/user.ts`, `stores/historyTable.ts`, `stores/neuroOl.ts`, `stores/navigation.ts`, `stores/layout.ts`.

HTTP‑клиент — [`front/src/utils/Api.ts`](front/src/utils/Api.ts) (axios).
**Важно:** запросы формируются **без** префикса `/api` (например `Api.get('products/...')`),
поэтому в проде нужен Nginx, проксирующий `/api/` на бэкенд, либо явный `VITE_API_URL`.

---

## Запуск

### Полный стек (Docker Compose)

```bash
# 1. Создать .env из шаблона
cp .env.example .env
# при необходимости отредактировать .env

# 2. Собрать и запустить все сервисы
docker compose up -d --build

# 3. Дождаться готовности Elasticsearch (~1–2 мин) и перезапустить бэкенд,
#    т.к. клиент ES инициализируется в момент импорта модулей
docker compose restart fastapi
```

> **Важно:** внешний порт Nginx может отличаться (в этой ветке проект поднимали на
> `8080`). Проверьте фактический порт командой `docker compose ps`.

После старта:

| Сервис | Адрес |
|--------|-------|
| Веб‑приложение | http://localhost:8080 |
| Документация API (Swagger) | http://localhost:8080/api/docs |
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |

### Логи

```bash
docker compose logs -f fastapi     # бэкенд
docker compose logs -f frontend    # фронтенд
docker compose logs -f nginx       # прокси
```

### Остановка

```bash
docker compose down          # остановить контейнеры
docker compose down -v       # остановить и удалить тома (данные БД/ES)
```

---

## Конфигурация

Переменные окружения задаются в `.env` (см. [`docker-compose.yaml`](docker-compose.yaml)):

| Переменная | Назначение |
|------------|-----------|
| `DOMAIN` | Домен/хост для Nginx (`NGINX_HOST`) |
| `HOST` | Базовый URL хоста |
| `user` / `pswd` | Учётные данные PostgreSQL, Redis, Elasticsearch |
| `POSTGRES_DB` | Имя БД PostgreSQL |
| `DB_HOST` / `POSTGRES_PORT` | Хост и порт БД |
| `key_api`, `model_type`, `vseGPTurl` | Параметры AI/GigaChat |
| `KIBANA_TOKEN` | Service‑account токен Kibana → Elasticsearch |

> Примечание: несмотря на переменные, строки подключения в
> [`app/TablePakage/model/database.py`](app/TablePakage/model/database.py) и
> [`app/StatisticsService/model/el_connect.py`](app/StatisticsService/model/el_connect.py)
> используют **захардкоженные** имена контейнеров `postgres`, `elasticsearch` и имя БД `pdb`.

---

## API

Интерактивная документация доступна в Swagger UI:
`GET http://localhost/api/docs` (openapi: `/api/openapi.json`).

Основные группы эндпоинтов (префикс `/api`):

- `/api/products` — продукты (CRUD, изображения)
- `/api/parameters` — схемы параметров
- `/api/tables`, `/api/parameter_values` — таблицы и значения
- `/api/module_search`, `/api/module_search_pandas` — подбор
- `/api/AI`, `/api/blocks` — распознавание и блоки
- `/api/tkp_generation` — генерация ТКП
- `/api/auth`, `/api/users`, `/api/roots` — авторизация, пользователи, роли
- `/api/requests` — заявки
- `/api/recognition_statistic`, `/api/selection_statistic` — статистика
- `/health` — проверка состояния бэкенда

---

## Генерация ТКП

Эндпоинт `POST /api/tkp_generation/create_tkp`:
1. Читает шаблон `.docx`/`.xlsx` из БД по `file_id`;
2. Сохраняет статистику подбора (номер документа, параметры);
3. Находит чертёж по «Маркировке» (`product_drawing`);
4. Подставляет значения параметров в плейсхолдеры `{{ ключ }}`;
5. Вставляет чертёж (InlineImage для Word / изображение для Excel);
6. Возвращает готовый файл через `StreamingResponse`.

Имя файла формируется по маске:
`TKP+TO_{ФИО Заказчика}_{Маркировка}_{id}`.

---

## Формулы (новая система расчёта)

Цель — упростить описание алгоритмов расчёта параметров. Алгоритмы и валидаторы
пишутся как **обычные Python‑функции** в [`app/formulas/algorithms.py`](app/formulas/algorithms.py)
и [`app/formulas/validators.py`](app/formulas/validators.py), а привязка параметра
к функциям хранится в **JSON‑поле** `formula_config` в БД:

```json
{ "func": "count_A", "validate": "validate_nonzero", "type": "formula" }
```

- `func` — имя функции расчёта из `algorithms.py`;
- `validate` — имя функции валидации из `validators.py`;
- `type` — `"formula"` для расчётных параметров.

### Пример функции расчёта

```python
def count_A(ctx):
    B = ctx.get("параметр Б")   # если не выбран — вернётся просьба заполнить
    V = ctx.get("параметр В")
    G = ctx.get("параметр Г")
    if G != 0:
        return B * V / G
    return "Параметр Г определен неверно, значение не может быть равным '0'!"
```

Значения зависимых параметров получаются через контекст:
- `ctx.get(name)` — **требует** значение; при отсутствии функция останавливается и
  в результат параметра возвращается `Заполните параметр "<имя>"`;
- `ctx.get_opt(name)` — возвращает `None`, если параметр не выбран;
- `ctx.num(name)` — как `get`, но с приведением к `float`.

### Валидация

Функция валидатора: `def validator(ctx, value) -> str | None`. Возвращает текст
ошибки или `None`. Может проверять другие параметры через `ctx`.

### Как это работает

1. Админ в карточке продукта указывает для формульного параметра (`type='Formula'`)
   имя функции расчёта и, при необходимости, валидатора — они сохраняются в
   `formula_config`.
2. При запросе `/api/module_search/process_table_data` новые формульные параметры
   вычисляются **асинхронно** (независимые формулы считаются параллельно через
   `asyncio.gather`, зависимости разрешаются по проходам).
3. Старые параметры (без `formula_config`) продолжают считаться прежним механизмом
   `CodeParametr` (**fallback** для совместимости).
4. Формат ответа API не меняется.

Список доступных функций бэкенд отдаёт через `GET /api/formula_functions`.

---

## Известные проблемы и ограничения

> Раздел основан на статическом анализе кода и фактическом запуске.

1. **Смешанные импорты в [`app/main.py`](app/main.py)** — используются и относительные
   (`.TablePakage...`), и абсолютные (`app.TableSearch...`) импорты. В контейнере
   FastAPI запуск выполнялся по import‑строке `app.main:app` (сработало), но для
   локального запуска вне docker надёжнее `uvicorn app.main:app` из корня репозитория.
2. **Захардкоженные имена контейнеров** (`postgres`, `elasticsearch`, БД `pdb`)
   в [`database.py`](app/TablePakage/model/database.py) и
   [`el_connect.py`](app/StatisticsService/model/el_connect.py) — локальный запуск
   вне docker‑сети требует `/etc/hosts` или изменения строк подключения.
3. **CORS‑middleware закомментирован** в [`app/main.py`](app/main.py) — прямой доступ
   фронтенда (:5173) к бэкенду (:8000) без Nginx будет заблокирован браузером.
4. **Kibana** требует `KIBANA_TOKEN` (service‑account token), которого нет в
   `.env.example`; токен создаётся через
   `elasticsearch-service-tokens create elastic/kibana kibana-token`.
5. В роутере [`router/products.py`](app/TablePakage/router/products.py) дублируется
   функция `generate_unique_filename`, есть комментарий о проблеме ручки
   `edit_product` (`ProductUpdate` без поля `params`).
6. Elasticsearch требует ≥ 1 GB heap и настройки `vm.max_map_count` (≥ 262144).
7. Фронтенд обращается к API **без** `/api` в путях — проксирование через Nginx
   обязательно, иначе запросы уходят на SPA вместо бэкенда. Для исправления собран
   фронтенд с `VITE_API_URL=/api` ([`front/Dockerfile`](front/Dockerfile)).
8. **Elasticsearch‑клиент может вернуть `None` при первом старте**: подключение
   выполняется в момент импорта [`el_connect.py`](app/StatisticsService/model/el_connect.py),
   а если ES ещё не готов, `create_elastic_client()` возвращает `None`, и startup падает
   в [`el_indexes.py`](app/StatisticsService/model/el_indexes.py) с
   `AttributeError: 'NoneType' object has no attribute 'indices'`. Лечится повторным
   `docker compose restart fastapi` после готовности ES.

---

## Временные изменения для локального тестирования

Для удобной проверки интерфейса без корпоративного Интранета и ES‑security в этой
ветке были внесены временные изменения (перед релизом их нужно вернуть):

- **Отключена проверка сессии** — [`get_user_id_by_session_id()`](app/UserService/utils/auth_utils.py)
  теперь всегда возвращает `4133` (администратор, максимальные права) вместо обращения
  к Redis/Интранету.
- **Отключена security Elasticsearch** (`xpack.security.enabled=false` в
  [`docker-compose.yaml`](docker-compose.yaml)), чтобы клиент ES подключался без пароля.
- **Фронтенд собирается с `VITE_API_URL=/api`** ([`front/Dockerfile`](front/Dockerfile)) —
  запросы идут через Nginx на FastAPI.
- Токен Kibana временно отключён (закомментирован `ELASTICSEARCH_SERVICEACCOUNTTOKEN`).

---

## Разработка

Рекомендуемый локальный сценарий для разработки (без полной пересборки фронта):

```bash
# Инфраструктура в Docker
docker compose up -d postgres redis elasticsearch

# Бэкенд локально (из корня репозитория)
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Фронтенд локально
cd front
npm install
npm run dev   # http://localhost:5173
```

> Для работы этого сценария потребуется настроить CORS (включить middleware либо
> использовать Nginx) и доступность имён `postgres`/`elasticsearch` с хоста.

---

## Лицензия

Информация о лицензии отсутствует. Проект предназначен для внутреннего использования.