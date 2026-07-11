"""
PillScan Database Connection
Async SQLAlchemy engine and session management for PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Create async engine
engine_kwargs = {
    "echo": settings.DATABASE_ECHO,
    "pool_pre_ping": True,
}

# pool_size and max_overflow are only supported by queue-based pools (like PostgreSQL)
if settings.DATABASE_URL.startswith("postgresql"):
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """
    Dependency injection for database sessions.
    Usage in routes: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all tables (development only — use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Columns added after the initial schema. ``create_all`` only creates *missing
# tables*, never new columns on existing ones, so for dev databases that already
# have a ``users`` table we add these idempotently on startup.
_ADDED_USER_COLUMNS = {
    "gemini_api_key": "TEXT",
    "openai_api_key": "TEXT",
    "llm_provider": "VARCHAR(10)",
}


async def ensure_new_columns():
    """
    Idempotently add newly-introduced columns to existing tables (dev only).

    Uses ``ADD COLUMN IF NOT EXISTS`` on PostgreSQL; on SQLite it checks
    PRAGMA table_info first. Safe to run on every startup.
    """
    from sqlalchemy import text

    is_postgres = settings.DATABASE_URL.startswith("postgresql")
    async with engine.begin() as conn:
        if is_postgres:
            for column, coltype in _ADDED_USER_COLUMNS.items():
                await conn.execute(
                    text(f'ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} {coltype}')
                )
        else:
            # SQLite has no "IF NOT EXISTS" for columns — introspect first.
            result = await conn.execute(text("PRAGMA table_info(users)"))
            existing = {row[1] for row in result.fetchall()}
            for column, coltype in _ADDED_USER_COLUMNS.items():
                if column not in existing:
                    await conn.execute(
                        text(f"ALTER TABLE users ADD COLUMN {column} {coltype}")
                    )


async def drop_tables():
    """Drop all tables (development/testing only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
