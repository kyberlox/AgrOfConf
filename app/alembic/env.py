import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from dotenv import load_dotenv

# --- Бутстрап путей импорта (важно: ДО импорта любых моделей).
# Модели в проекте используют СМЕШАННЫЕ стили импорта:
#   * `from TablePakage.model...`          — нужен каталог app в sys.path
#   * `from app.TablePakage.model...`      — нужен КОРЕНЬ проекта (родитель app)
# env.py лежит в <root>/app/alembic/, поэтому:
#   parents[1] = каталог app (содержит TablePakage, UserService, ...)
#   parents[2] = корень проекта (содержит пакет app/)
# Это работает и при монтировании всего репозитория, и при монтировании только app/.
_BOOTSTRAP = Path(__file__).resolve().parents
for _p in (str(_BOOTSTRAP[2]), str(_BOOTSTRAP[1])):
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv()
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ВАЖНО: все импорты ЕДИНООБРАЗНО с префиксом `app.`.
# Некоторые модели (Roots.py, Users.py, psql_models.py) внутри сами делают
# `from app.TablePakage.model.database import Base`. Если здесь импортировать
# `from TablePakage.model...` — Python загрузит ДВА разных модуля database.py
# и создаст ДВА разных Base, и таблицы части моделей не попадут в metadata.
# Единый префикс гарантирует один и тот же модуль и один Base.

# Базовый класс моделей (единый для всего проекта).
from app.TablePakage.model.database import Base

# --- Модели. ВАЖНО: импорт класса регистрирует таблицу в Base.metadata.
# Без этих импортов alembic autogenerate не увидит таблицы.
# TablePakage (10 таблиц):
from app.TablePakage.model.product import Product
from app.TablePakage.model.datamart import DataMartRegistry
from app.TablePakage.model.tkp import TKP
from app.TablePakage.model.product_table import ProductTable
from app.TablePakage.model.product_table_ver import ProductTableVersion
from app.TablePakage.model.parameter_block import ParameterBlock
from app.TablePakage.model.parameter_file import ParameterFile
from app.TablePakage.model.parameter_schema import ParameterSchema
from app.TablePakage.model.product_drawing import ProductDrawing
from app.TablePakage.model.product_files import ProductFiles
# UserService (2 таблицы):
from app.UserService.model.Users import Users
from app.UserService.model.Roots import Roots
# RequestService (3 таблицы):
from app.RequestService.model.request import Request
from app.RequestService.model.customer import Customer
from app.RequestService.model.contact_person import ContactPerson
# StatisticsService (2 таблицы):
from app.StatisticsService.model.psql_models import RecognitionModel, SelectionModel

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url() -> str:
    """
    Собирает DSN для async-подключения.
    В docker-compose хост БД — это имя сервиса (postgres), не localhost.
    Имена переменных совпадают с app/TablePakage/model/database.py
    (поддерживаются оба написания хоста: DBHOST и DB_HOST).
    """
    user = os.getenv("user", "postgres")
    pswd = os.getenv("pswd", "postgres")
    return f'postgresql+asyncpg://{user}:{pswd}@postgres/pdb'

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # sqlalchemy.url в alembic.ini закомментирован — берём URL из env-переменных.
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # В ini файле sqlalchemy.url закомментирован, поэтому подставляем URL
    # из переменных окружения до создания движка.
    config.set_main_option("sqlalchemy.url", get_url())

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
