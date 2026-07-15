"""
Tests for admin-shared Gemini keys.

An admin who stores a Gemini key in their AI settings shares it with every user,
so a regular user (with no key of their own) can still use pill ID / assistant /
leaflet. Personal keys stay private to the sync resolver.
"""

import uuid
import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import llm_keys
from app.models.user import User
from app.utils.crypto import encrypt_secret


def _user(**kw) -> User:
    base = dict(
        id=uuid.uuid4(),
        password_hash="h",
        full_name="X",
        language="ar",
        role="USER",
        status="APPROVED",
        is_admin=False,
    )
    base.update(kw)
    return User(**base)


@pytest.mark.asyncio
async def test_admin_key_shared_with_regular_user(db_session: AsyncSession):
    admin = _user(
        email="admin@share.sa", phone="+966500000100",
        role="ADMIN", is_admin=True,
        gemini_api_key=encrypt_secret("ADMIN-SHARED-KEY"),
    )
    regular = _user(email="user@share.sa", phone="+966500000101")
    db_session.add_all([admin, regular])
    await db_session.commit()

    keys = await llm_keys.resolve_gemini_keys_async(regular, db_session)
    assert "ADMIN-SHARED-KEY" in keys


@pytest.mark.asyncio
async def test_sync_resolver_excludes_admin_keys(db_session: AsyncSession):
    """The synchronous resolver only sees the user's own keys (+ env), not admins'."""
    regular = _user(email="user2@share.sa", phone="+966500000102")
    # Regular user has no key of their own → sync resolver returns nothing.
    assert llm_keys.resolve_gemini_keys(regular) == []


@pytest.mark.asyncio
async def test_no_admin_key_means_no_shared_key(db_session: AsyncSession):
    admin = _user(email="admin2@share.sa", phone="+966500000103", role="ADMIN", is_admin=True)
    regular = _user(email="user3@share.sa", phone="+966500000104")
    db_session.add_all([admin, regular])
    await db_session.commit()

    keys = await llm_keys.resolve_gemini_keys_async(regular, db_session)
    assert keys == []
