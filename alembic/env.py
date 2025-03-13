from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context

# 导入配置和模型
from app.models import *  # 导入所有模型
from app.db.base import Base
from app.core.database_config import get_db_url
import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 获取数据库URL
db_url = get_db_url()

# 设置数据库URL
config.set_main_option("sqlalchemy.url", db_url)

# 如果是SQLite，设置特殊配置
if db_url.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    config.set_section_option("alembic", "sqlalchemy.pool_class", "sqlalchemy.pool.StaticPool")
    config.set_section_option("alembic", "sqlalchemy.connect_args", '{"check_same_thread": false}')

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 获取数据库 URL
    url = config.get_main_option("sqlalchemy.url")
    
    # 创建引擎配置
    engine_args = {}
    
    # 如果是 SQLite，添加特殊配置
    if url.startswith("sqlite"):
        engine_args["connect_args"] = {"check_same_thread": False}
        engine_args["poolclass"] = pool.StaticPool
    
    # 直接创建引擎，避免使用 engine_from_config
    connectable = create_engine(url, **engine_args)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
