"""
PillScan — Alembic Migrations Environment
==========================================

Configures Alembic to use our async SQLAlchemy engine and discover
all models via the shared Base metadata.

Usage:
    # Generate a new migration
    alembic revision --autogenerate -m "description"
    
    # Apply all pending migrations
    alembic upgrade head
    
    # Rollback one migration
    alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import our app's Base and all models so Alembic can detect table changes
from app.database import Base
from app.models.user import User
from app.models.drug import Drug, DrugImage, DrugSideEffect, DrugContraindication
from app.models.medication import Medication
from app.models.reminder import Reminder
from app.models.scan_history import ScanHistory
from app.models.adherence import AdherenceLog

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL scripts without DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations using async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
