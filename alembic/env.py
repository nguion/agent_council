# AI Generated Code by Deloitte + Cursor (BEGIN)
from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from alembic import context

# Add src to path so we can import our models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Base and models
from src.web.database import Base, DATABASE_URL, IS_SQLITE, IS_POSTGRES

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata for autogenerate support
target_metadata = Base.metadata

# Override sqlalchemy.url from environment if present
# Alembic needs a sync URL, so convert async URL to sync
database_url = os.getenv("DATABASE_URL", DATABASE_URL)
if database_url.startswith("sqlite+aiosqlite"):
    # Convert async SQLite URL to sync
    sync_url = database_url.replace("sqlite+aiosqlite", "sqlite")
elif database_url.startswith("postgresql+asyncpg"):
    # Convert async PostgreSQL URL to sync
    sync_url = database_url.replace("postgresql+asyncpg", "postgresql")
else:
    sync_url = database_url

config.set_main_option("sqlalchemy.url", sync_url)


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

    In this scenario we need to create a sync Engine
    and associate a connection with the context.

    """
    # Create sync engine for migrations (Alembic doesn't support async directly)
    from sqlalchemy import create_engine
    
    url = config.get_main_option("sqlalchemy.url")
    
    # Configure engine based on DB type
    connect_args = {}
    if IS_SQLITE:
        connect_args = {
            "timeout": 30,
            "check_same_thread": False
        }
    
    engine = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
        echo=False
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
# AI Generated Code by Deloitte + Cursor (END)
