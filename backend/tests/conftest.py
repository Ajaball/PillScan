"""
PillScan — Test Configuration & Fixtures
=========================================

Provides async test database, test client, and authenticated user fixtures
for all backend unit and integration tests.

Architecture Decision:
- Using SQLite in-memory for test isolation (no PostgreSQL dependency)
- Each test function gets a fresh database via function-scoped fixtures
- httpx.AsyncClient replaces requests for async FastAPI testing
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.services.auth_service import hash_password, create_access_token

# ── Test Database Engine (SQLite in-memory) ───────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_pillscan.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override the production database dependency with test database."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Override the FastAPI dependency
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Direct database session for test setup/assertions."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """Create a test user and return their data + access token."""
    from app.models.user import User
    import uuid

    user_uuid = uuid.uuid4()
    user = User(
        id=user_uuid,
        email="testuser@pillscan.sa",
        full_name="مستخدم تجريبي",
        password_hash=hash_password("Test@1234"),
        language="ar",
        role="USER",
        status="APPROVED",
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()

    access_token = create_access_token(str(user_uuid), user.email)

    return {
        "id": str(user_uuid),
        "email": user.email,
        "full_name": user.full_name,
        "password": "Test@1234",
        "access_token": access_token,
        "auth_header": {"Authorization": f"Bearer {access_token}"},
    }


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> dict:
    """Create an admin user for testing admin-only endpoints."""
    from app.models.user import User
    import uuid

    user_uuid = uuid.uuid4()
    user = User(
        id=user_uuid,
        email="admin@pillscan.sa",
        full_name="مدير النظام",
        password_hash=hash_password("Admin@1234"),
        language="ar",
        role="ADMIN",
        status="APPROVED",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()

    access_token = create_access_token(str(user_uuid), user.email)

    return {
        "id": str(user_uuid),
        "email": user.email,
        "access_token": access_token,
        "auth_header": {"Authorization": f"Bearer {access_token}"},
    }
