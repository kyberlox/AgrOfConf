# Конфигуратор ПК (SaveOfConf / Agregator)

> Платформа подбора и конфигурирования запорно‑регулирующей арматуры с генерацией ТКП
> (технико‑коммерческого предложения) по продуктам, параметрическим таблицам и чертежам.

Проект состоит из **FastAPI‑бэкенда**, **Vue 3‑фронтенда** и вспомогательной
инфраструктуры (PostgreSQL, Redis, Elasticsearch, Kibana, Nginx), объединяемых через
`docker-compose.yaml`. Система позволяет администратору вести каталог продукции
(«ОЛ» — оборудование), настраивать параметры, блоки и таблицы подбора, а инженеру —
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
- [Формулы (новая система расчёта)](#формулы-новая-система-расчёта)
- [Известные проблемы и ограничения](#известные-проблемы-и-ограничения)
- [Временные изменения для локального тестирования](#временные-изменения-для-локального-тестирования)
- [Разработка](#разработка)

---

## Возможности

- **Каталог продукции** — создание/редактирование товаров, загрузка изображений
  (base64/`UploadFile`), чертежей, сертификатов и файлов, управление версиями таблиц
  (до 5 версий).
- **Параметризация изделия** — динамические схемы параметров (типы `Table`,
  `Formula`, `Drawing`, `File`), транслитерация имён, сортировка, видимость по ролям
  (`field_of_view`), флаги `editable`, привязка к блокам.
- **Блоки параметров** — группировка параметров в блоки, управление
  `editable`/`visibility`, контакты изделия.
- **Подбор по таблицам** — последовательный (каскадный) выбор параметров по данным
  Excel‑таблиц (datamart), SQL‑агрегация доступных значений, поиск ошибок подбора.
- **Свободный режим** конфигурирования без обязательной последовательности.
- **Распознавание опросных листов (ОЛ)** — загрузка документов
  (`/api/AI/upload_OL`), нейросетевая обработка (OpenAI‑совместимый клиент:
  GigaChat/deepseek), сравнение распознанных значений с базой.
- **Статистика** — сбор событий распознавания и подборов в Elasticsearch, витрины,
  графики (chart.js) в веб‑интерфейсе.
- **Генерация ТКП** — подстановка данных конфигурации в шаблоны `.docx`/`.xlsx`,
  вставка чертежа, формирование номера документа и сохранение статистики.
- **Перенос продуктов** — экспорт полной конфигурации продукта (таблицы, файлы,
  параметры) в ZIP и импорт обратно.
- **Авторизация через корпоративный Интранет** — сессии в Redis, синхронизация
  пользователей и ролей. Для локальной разработки есть **DEV‑сессия**
  (см. [Конфигурацию](#конфигурация)).
- **Заявки** — многостадийный жизненный цикл заявок с заказчиками, контактными
  лицами, сроками и процедурами.
- **Новая система формул** — расчёт и валидация параметров Python‑функциями
  через `formula_config` (см. [Формулы](#формулы-новая-система-расчёта)).

---

## Архитектура

```
                    ┌────────────────────────────────────────────────┐
    Браузер         │              Nginx :8080 (внешний порт)         │
   (Vue 3 SPA) ────►│  /            → frontend :5173 (Vite preview)  │
                    │  /api/        → fastapi :8000 (FastAPI/Uvicorn)│
                    └────────────────────────────────────────────────┘
                                     │
                      ┌──────────────┼──────────────────────┐
                      ▼              ▼                      ▼
               ┌────────────┐  ┌──────────┐          ┌───────────────┐
               │ PostgreSQL │  │  Redis   │          │ Elasticsearch │
               │ :5432      │  │ :6379    │          │ :9200 / :9300 │
               │ БД pdb     │  │ сессии   │          │ статистика    │
               └────────────┘  └──────────┘          └───────┬───────┘
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
- Python 3.13, FastAPI 0.136 (CLI `fastapi run`), Uvicorn 0.38
- SQLAlchemy 2.0 (async, `asyncpg`), psycopg2
- Redis (`redis`), Elasticsearch 9.1 (`elasticsearch` py‑клиент)
- docxtpl, openpyxl, pypandoc, PyMuPDF, Pillow
- OpenAI‑SDK (`openai`, `AsyncOpenAI`) для распознавания (GigaChat/deepseek),
  httpx, requests
- pandas, alembic, python-dotenv, transliterate, aiofiles

**Фронтенд (`front/`)**
- Vue 3.5, Vue Router 5, Pinia 3
- Vite 7, TypeScript 5.9, Tailwind CSS 4
- ag‑grid‑vue3 (таблицы), chart.js / vue-chartjs (графики)
- vue3-toastify, vue-draggable-plus, vuedraggable, vue-image-zoomer,
  beans-ui-kit, @vueuse/core, downloadjs
- axios

**Инфраструктура**
- Nginx 1.27 (reverse proxy + CORS, клиентский лимит 1024M)
- PostgreSQL 18.1, Redis (alpine, с паролем), Elasticsearch 9.1, Kibana 9.1

---

## Структура репозитория

```
.
├── docker-compose.yaml          # Оркестрация всех сервисов (сеть app-network)
├── .env.example                 # Шаблон переменных окружения
├── nginx/default.conf           # Reverse‑proxy: фронт + /api (порт 8080)
├── restart.sh                   # git pull + перезапуск fastapi
├── restart_front.sh             # пересборка и перезапуск frontend
├── plans/                       # Документы о планах (new_formula_system.md)
├── uploads/                     # Смонтированный том для загрузок
├── app/                         # Бэкенд FastAPI (пакет `app`)
│   ├── main.py                  # Точка входа, подключение роутеров, startup‑миграции
│   ├── logging_config.py        # Логирование (RotatingFileHandler)
│   ├── requirements.txt
│   ├── Dockerfile               # python:3.13, CMD fastapi run main.py
│   ├── tempates/                # Базовые шаблоны ТКП (.docx/.xlsx)
│   ├── static/                  # Динамические файлы (изображения, чертежи, версии)
│   ├── formulas/                # Новая система расчёта формул (algorithms, validators)
│   ├── TablePakage/             # Каталог продукции, параметры, ТКП, перенос
│   ├── TableSearch/             # Подбор по таблицам, ИИ, распознавание
│   ├── UserService/             # Пользователи, роли, сессии, авторизация, DEV‑сессия
│   ├── StatisticsService/       # Статистика (Elasticsearch, репозиторий)
│   └── RequestService/          # Заявки, заказчики, контактные лица
└── front/                       # SPA Vue 3 (`name: "agregator"`)
    ├── Dockerfile               # node:22, сборка без type-check (build-only)
    ├── vite.config.ts
    ├── package.json
    └── src/
        ├── main.ts
        ├── App.vue              # Layout: LeftSidebar + RouterView, authorize()
        ├── router/index.ts
        ├── stores/              # Pinia: configurator, products, user, neuroOl, ...
        ├── utils/Api.ts         # Axios‑клиент (baseURL = VITE_API_URL)
        ├── composables/
        ├── components/          # Общие компоненты (layout, лоадеры, модалки)
        ├── assets/              # interfaces, static (фичи, навигация), style/css
        └── views/
            ├── homeView/        # Заявки, распознавание, статистика
            ├── configurator/    # Страница конфигуратора (ключевой модуль)
            ├── admin/           # Админка: продукты, параметры, блоки
            └── userPage/        # Профиль пользователя
```

---

## Бэкенд: модули

### `TablePakage` — каталог, параметры, таблицы, ТКП, перенос

| Файл | Назначение |
|------|-----------|
| `router/products.py` | CRUD продуктов, загрузка изображений/чертежей/файлов (base64/UploadFile), zip‑выгрузка |
| `router/parameters.py` | CRUD схем параметров, создание/переименование колонок таблиц, файлы параметра |
| `router/tables.py` | Работа с таблицами продукта (загрузка Excel, версии до 5, скачивание XLSX) |
| `router/parameter_values.py` | Уникальные значения, добавление/изменение/удаление значений параметра |
| `router/tkp_generation.py` | Генерация ТКП из шаблонов docx/xlsx, история ТКП, шаблоны |
| `router/product_porting.py` | Экспорт/импорт продукта в ZIP (`/api/products/{id}/export`, `/api/products/import`) |
| `utils/*` | `kir_param_to_latin`, `db_utils`, `router_utils` |
| `model/*` | ORM: `Product`, `ParameterSchema`, `DataMartRegistry`, `ProductTable`, `ProductTableVer`, `TKP`, файлы, чертежи, блоки параметров + миграции (`formula_config`, `blocks`, `parameter_flags`) |

### `TableSearch` — поиск и подбор

| Файл | Назначение |
|------|-----------|
| `router/module_search.py` | Каскадный подбор по таблицам (`POST /api/module_search/process_table_data`), SQL‑агрегации, формулы |
| `router/module_search_pandas.py` | **Неактивен** — единственный маршрут закомментирован (мёртвый код) |
| `router/AI.py` | Нейросетевое распознавание ОЛ (OpenAI‑совместимый): `/upload_OL`, `/convert-ai-result` |
| `router/blocks.py` | CRUD блоков параметров, assign/unassign, контакты, порядок |
| `utils/*` | Конвертация ОЛ, поиск формул, промпты, работа с datamart |
| `model/database_pandas.py` | Синхронный движок для pandas (не используется) |

### `formulas` — новая система расчёта формул

| Файл | Назначение |
|------|-----------|
| `algorithms.py` | Библиотека функций расчёта (например `count_A`, `area_of_circle`) |
| `validators.py` | Библиотека функций валидации (например `validate_nonzero`) |
| `engine.py` | Ядро: `FormulaContext`, асинхронный решатель зависимостей (`asyncio.gather`) |
| `registry.py` | Реестры имён функций (безопасный вызов по имени из БД) |
| `router.py` | Эндпоинт `/api/formula_functions` (список доступных функций) |
| `integration.py` | Интеграция в `module_search` (новые формулы + fallback), разрешение чертежей |

### `UserService` — пользователи и сессии

| Файл | Назначение |
|------|-----------|
| `router/auth_router.py` | Авторизация через Интранет (`/auth/redirect`), `/auth/user_id_by_session_id` |
| `router/users_router.py` | CRUD пользователей, `product_users` |
| `router/roots_router.py` | Роли/права (`create_new_root`, `access_base`, `access_admin`) |
| `services/redis_service.py` | Хранение сессий в Redis |
| `utils/auth_utils.py` | Проверка сессии, refresh, зависимость `get_user_id_by_session_id` |
| `utils/dev_session.py` | DEV‑сессия (включ/выкл через `DEV_SESSION_ENABLED`) + создание dev‑пользователя |

### `StatisticsService` — статистика

| Файл | Назначение |
|------|-----------|
| `router/recognition_router.py` | Статистика распознавания (`upload`, `all`, `get_by_user_id`, ...) |
| `router/selection_router.py` | Статистика подборов (`selection`, `update_status`, `metrics`, `monthly_comparison`, `search_by_value`, `search_by_key_and_value`) |
| `repo/*` | Абстрактный репозиторий + реализации (Elasticsearch — активная, Mongo и Postgres — заготовки) |
| `model/el_connect.py` | Клиент ES с ретраями и `ensure_elastic_ready()` (ожидание готовности при старте) |
| `model/el_indexes.py` | Создание индексов `selection_index`, `recognition_index` (русский анализатор) |
| `set/settings.py` | Имена индексов |

### `RequestService` — заявки

| Файл | Назначение |
|------|-----------|
| `router/requests.py` | Жизненный цикл заявок: CRUD `/api/requests`, поиск заказчиков/контактов, заявки пользователя |
| `model/*` | ORM: `Request`, `Customer`, `ContactPerson` |

---

## Фронтенд

Точка входа — `front/src/main.ts`. Роутер `front/src/router/index.ts` определяет страницы:

| Путь | Страница |
|------|----------|
| `/login` | Открывает Интранет `https://intranet.emk.ru/api/auth_router/argconf` |
| `/` | Редирект на `/my_requests` |
| `/my_requests`, `/ko_requests` | `HomeView.vue` (заявки, распознавание, статистика) |
| `/configurator/:id` | `Configurator.vue` (ключевой модуль) |
| `/admin` | Админка: список продуктов |
| `/admin/product/:id` | `Product.vue` (параметры, блоки, таблицы, ТКП) |
| `/user/:id` | Профиль пользователя |

Ключевой модуль платформы — **страница конфигуратора**
`front/src/views/configurator/Configurator.vue` и её компоненты `EngineParams*`.
Здесь инженер последовательно выбирает параметры, видит доступные значения
(обновляются каскадно), чертёж и «Маркировку», а в конце формирует ТКП.

Состояние хранится в Pinia‑сторах:
- `stores/configurator.ts` — параметры, статус, маркировка, чертёж, ошибки;
- `stores/products.ts` — список продуктов;
- `stores/user.ts`, `stores/historyTable.ts`, `stores/neuroOl.ts`, `stores/navigation.ts`, `stores/layout.ts`.

HTTP‑клиент — `front/src/utils/Api.ts` (axios). **Важно:** в путях запросов префикса
`/api` **нет** (например `Api.get('products/...')`), а `baseURL` берётся из
`VITE_API_URL`. В Docker фронт собирается с `VITE_API_URL=/api`, поэтому все запросы
идут через Nginx (`location /api/`) на FastAPI. При локальной разработке (`npm run dev`)
нужно либо задать `VITE_API_URL=http://localhost:8000` и настроить CORS на бэкенде,
либо продолжать ходить через Nginx.

---

## Запуск

### Полный стек (Docker Compose)

```bash
# 1. Создать .env из шаблона
cp .env.example .env
# при необходимости отредактировать .env (см. «Конфигурация»)

# 2. Настроить систему под Elasticsearch (один раз, на хосте):
#    vm.max_map_count для ES ≥ 262144
sudo sysctl -w vm.max_map_count=262144
# (постоянно — в /etc/sysctl.conf)

# 3. Собрать и запустить все сервисы
docker compose up -d --build
```

При старте бэкенд (`app/main.py`, `startup_event`):
1. создаёт таблицы в PostgreSQL (`create_tables`);
2. применяет лёгкие миграции: `formula_config`, блоки параметров, флаги параметров;
3. создаёт DEV‑пользователя и admin‑роль, если включена DEV‑сессия;
4. **ждёт готовности Elasticsearch** (`ensure_elastic_ready()`, до 10 минут) и
   создаёт индексы `selection_index` / `recognition_index`.

> Повторный `docker compose restart fastapi` после старта ES в этой ветке **не
> требуется** — ожидание готовности ES встроено в стартап. Он нужен только в том
> случае, если бэкенд упал по другой причине (см. [Известные проблемы](#известные-проблемы-и-ограничения)).

После старта:

| Сервис | Адрес |
|--------|-------|
| Веб‑приложение | http://localhost:8080 |
| Документация API (Swagger) | http://localhost:8080/api/docs |
| Бэкенд (напрямую) | http://localhost:8000 |
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |

### Логи

```bash
docker compose logs -f fastapi     # бэкенд (том app_logs/fastapi)
docker compose logs -f frontend    # фронтенд
docker compose logs -f nginx       # прокси (том app_logs/nginx)
docker compose logs -f postgres    # БД (том app_logs/postgres)
```

### Остановка

```bash
docker compose down          # остановить контейнеры
docker compose down -v       # остановить и удалить тома (данные БД/ES)
```

---

## Конфигурация

Переменные окружения задаются в `.env` (см. `.env.example` и `docker-compose.yaml`):

| Переменная | Назначение |
|------------|-----------|
| `DOMAIN` | Домен/хост для Nginx (`NGINX_HOST`) |
| `HOST` | Базовый URL хоста |
| `user` / `pswd` | Учётные данные PostgreSQL (и пароль Redis); `elastic` в ES использует `pswd` |
| `POSTGRES_DB` | Имя БД PostgreSQL (по умолчанию `pdb`) |
| `DB_HOST` / `POSTGRES_PORT` | Хост и порт БД (**не используются** — см. примечание ниже) |
| `key_api`, `model_type`, `vseGPTurl` | Параметры нейросети (OpenAI‑совместимый URL и ключ) |
| `KIBANA_TOKEN` | Service‑account токен Kibana → Elasticsearch (в этой ветке не используется, т.к. security ES отключена) |
| `DEV_SESSION_ENABLED` | Включает DEV‑сессию (`true` — по умолчанию): `get_user_id_by_session_id()` всегда возвращает `DEV_USER_ID` |
| `DEV_USER_ID` | ID dev‑пользователя (по умолчанию `4133`, создаётся при старте с admin‑правами) |

> **Примечание:** несмотря на `DB_HOST`/`POSTGRES_PORT`, строки подключения в
> `app/TablePakage/model/database.py` и `app/StatisticsService/model/el_connect.py`
> используют **захардкоженные** имена контейнеров `postgres`, `elasticsearch` и имя
> БД `pdb`. Учётные данные (`user`/`pswd`) берутся из `.env`.

---

## API

Интерактивная документация доступна в Swagger UI:
`GET http://localhost:8080/api/docs` (openapi: `/api/openapi.json`).

Основные группы эндпоинтов (префикс `/api`):

- `/api/products` — продукты (CRUD, изображения, чертежи, файлы, zip)
- `/api/products/{id}/export`, `/api/products/import` — перенос продукта (ZIP)
- `/api/parameters` — схемы параметров (в т.ч. `/sort/{product_id}`, файлы параметра)
- `/api/tables`, `/api/parameter_values` — таблицы, версии, значения
- `/api/module_search/process_table_data` — каскадный подбор (активный маршрут; pandas‑аналог отключён)
- `/api/AI` — распознавание ОЛ (`/upload_OL`, `/convert-ai-result`)
- `/api/blocks` — блоки параметров (CRUD, assign/unassign, контакты)
- `/api/tkp_generation` — генерация ТКП, история, шаблоны
- `/api/formula_functions` — список доступных функций расчёта и валидации
- `/api/auth`, `/api/users`, `/api/roots` — авторизация, пользователи, роли
- `/api/requests` — заявки, поиск заказчиков/контактов
- `/api/recognition_statistic` — статистика распознавания
- `/api/selection_statistic` — статистика подборов (`/selection`, `/metrics`,
  `/monthly_comparison`, `/search_by_value`, `/search_by_key_and_value`)
- `/api/files/*` — статические файлы (изображения, чертежи)
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

Дополнительные эндпоинты: `create_history_tkp` (ТКП из истории), `add`,
`get_tkp_of_product/{product_id}`, `delete` — управление шаблонами.

---

## Формулы (новая система расчёта)

Цель — упростить описание алгоритмов расчёта параметров. Алгоритмы и валидаторы
пишутся как **обычные Python‑функции** в `app/formulas/algorithms.py`
и `app/formulas/validators.py`, а привязка параметра к функциям хранится в
**JSON‑поле** `formula_config` в БД (колонка создаётся миграцией при старте):

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
   `asyncio.gather`, зависимости разрешаются по проходам; циклы обрабатываются).
3. Старые параметры (без `formula_config`) продолжают считаться прежним механизмом
   (**fallback** для совместимости).
4. Формат ответа API не меняется.

Список доступных функций бэкенд отдаёт через `GET /api/formula_functions`.

---

## Известные проблемы и ограничения

> Раздел основан на статическом анализе кода и фактическом запуске (ветка `full_new`).

1. **Относительные импорты в `app/main.py`** — бэкенд является пакетом `app` и
   запускается командой `uvicorn app.main:app` **из корня репозитория**. Для
   локального запуска вне Docker используйте именно эту команду. В `app/Dockerfile`
   указан `fastapi run main.py` (WORKDIR `/data/app`) — если при относительных
   импортах запуск падает, переопределите команду контейнера на
   `uvicorn app.main:app --host 0.0.0.0 --port 8000` (с `PYTHONPATH=/data` или
   `--app-dir /data`, так как монтируется `./app` → `/data/app`).
2. **Захардкоженные имена контейнеров** (`postgres`, `elasticsearch`, БД `pdb`)
   в `app/TablePakage/model/database.py` и `app/StatisticsService/model/el_connect.py` —
   локальный запуск вне docker‑сети требует `/etc/hosts` или изменения строк подключения.
   `DB_HOST`/`POSTGRES_PORT` из `.env` фактически не используются.
3. **CORS‑middleware закомментирован** в `app/main.py` — прямой доступ фронтенда
   (:5173) к бэкенду (:8000) без Nginx будет заблокирован браузером. Обращение идёт
   обязательно через Nginx.
4. **Пункт про `KIBANA_TOKEN` в этой ветке неактуален**: security Elasticsearch
   **отключена** (`xpack.security.enabled=false`), токен в `docker-compose.yaml`
   закомментирован. Токен понадобится только при повторном включении security
   (`elasticsearch-service-tokens create elastic/kibana kibana-token`).
5. В `app/TablePakage/router/products.py` дублируется функция
   `generate_unique_filename` (строки 69 и 75), есть комментарий о проблеме ручки
   `edit_product` (`ProductUpdate` без поля `params`).
6. Elasticsearch требует ≥ 1 GB heap (задано `ES_JAVA_OPTS=-Xms1g -Xmx1g`) и
   настройки `vm.max_map_count` (≥ 262144) на хосте — иначе контейнер не стартует.
7. Фронтенд обращается к API **без** `/api` в путях — проксирование через Nginx
   обязательно, иначе запросы уходят на SPA вместо бэкенда. Для этого фронт
   собирается с `VITE_API_URL=/api` (`front/Dockerfile`).
8. **Порты опубликованы на внешнем интерфейсе** (5432, 9200/9300, 5173, 5601).
   Для продакшена стоит заменить на `127.0.0.1:PORT:PORT` (как сделано для Redis и
   FastAPI), чтобы не открывать БД и Elasticsearch наружу.
9. **`front/package.json`**: полная сборка `npm run build` падает на `vue-tsc`
   type-check (предсуществующие TS‑ошибки) — поэтому Docker использует
   `npm run build-only`. Запускать именно так.
10. **Исправлено в текущей ветке** — ранее ES‑клиент мог вернуть `None` при первом
    старте и ронять приложение в `el_indexes.py` (`AttributeError`). Теперь стартап
    вызывает `ensure_elastic_ready()` (ожидание до 10 минут) и лишь затем создаёт
    индексы. Если старт всё же падает — проверьте логи: `docker compose logs fastapi`.

---

## Временные изменения для локального тестирования

Для удобной проверки интерфейса без корпоративного Интранета и ES‑security в этой
ветке внесены временные изменения (перед релизом их нужно вернуть):

- **DEV‑сессия** — `get_user_id_by_session_id()` при `DEV_SESSION_ENABLED=true`
  (по умолчанию) возвращает `DEV_USER_ID` (4133, администратор) вместо обращения к
  Redis/Интранету. Отключается флагом `DEV_SESSION_ENABLED=false` в `.env`.
  При старте автоматически создаётся dev‑пользователь и admin‑роль
  (`ensure_dev_user`).
- **Отключена security Elasticsearch** (`xpack.security.enabled=false` в
  `docker-compose.yaml`), чтобы клиент ES подключался без пароля. Токен Kibana
  закомментирован.
- **Фронтенд собирается с `VITE_API_URL=/api`** (`front/Dockerfile`) — запросы идут
  через Nginx на FastAPI.
- **CORS закомментирован** в `app/main.py` — доступ только через Nginx.

---

## Разработка

Рекомендуемый локальный сценарий для разработки (без полной пересборки фронта):

```bash
# 0. Настройка ES на хосте (один раз)
sudo sysctl -w vm.max_map_count=262144

# Инфраструктура в Docker
docker compose up -d postgres redis elasticsearch

# Бэкенд локально (ИЗ КОРНЯ репозитория — важно для относительных импортов)
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Фронтенд локально
cd front
npm install
npm run dev   # http://localhost:5173
```

> Для этого сценария потребуется настроить CORS (включить middleware в
> `app/main.py` либо использовать Nginx: `docker compose up -d nginx frontend`)
> и обеспечить доступность имён `postgres`/`elasticsearch` с хоста (например,
> добавить в `/etc/hosts`: `127.0.0.1 postgres elasticsearch`, предварительно
> опубликовав порты на `127.0.0.1`). Альтернатива — поднимать бэкенд тоже в Docker
> и править код через смонтированный том `./app:/data/app`.

Рабочие скрипты в репозитории:
- `restart.sh` — `git pull` + перезапуск `fastapi` + логи;
- `restart_front.sh` — пересборка и перезапуск `frontend`.

---

## Лицензия

Информация о лицензии отсутствует. Проект предназначен для внутреннего использования.