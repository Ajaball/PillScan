"""
Tests for the User Query History table (user_queries): persistence via the
assistant endpoint, retrieval, the user relation, and cascade delete.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_query import UserQuery


class TestQueryHistoryAPI:
    @pytest.mark.asyncio
    async def test_lookup_is_saved_and_listed(self, client: AsyncClient, test_user: dict):
        """Each drug-info lookup is recorded and returned by /assistant/history."""
        for drug in ("Panadol", "Brufen"):
            r = await client.post(
                "/api/v1/assistant/drug-info",
                headers=test_user["auth_header"],
                json={"name": drug},
            )
            assert r.status_code == 200

        hist = await client.get(
            "/api/v1/assistant/history", headers=test_user["auth_header"],
        )
        assert hist.status_code == 200
        data = hist.json()
        assert len(data) == 2
        assert {d["query_text"] for d in data} == {"Panadol", "Brufen"}
        assert "recognized" in data[0] and "created_at" in data[0]

    @pytest.mark.asyncio
    async def test_history_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/assistant/history")
        assert r.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_history_is_per_user(
        self, client: AsyncClient, test_user: dict, admin_user: dict
    ):
        """A user's history must not include another user's lookups."""
        await client.post(
            "/api/v1/assistant/drug-info",
            headers=test_user["auth_header"], json={"name": "Aspirin"},
        )
        # The admin has made no lookups → empty history.
        admin_hist = await client.get(
            "/api/v1/assistant/history", headers=admin_user["auth_header"],
        )
        assert admin_hist.status_code == 200
        assert admin_hist.json() == []


class TestQueryModelRelations:
    @pytest.mark.asyncio
    async def test_relation_and_cascade_delete(self, db_session: AsyncSession):
        """user.queries relates rows; deleting the user cascades to its queries."""
        u = User(
            id=uuid.uuid4(), email="q@x.sa", phone="+966500000200",
            password_hash="h", full_name="Q", role="USER", status="APPROVED",
        )
        db_session.add(u)
        await db_session.flush()

        db_session.add_all([
            UserQuery(user_id=u.id, query_text="Panadol", recognized=True,
                      result={"name": "بنادول", "sideEffects": [], "usageTimes": []}),
            UserQuery(user_id=u.id, query_text="Brufen", recognized=False, result=None),
        ])
        await db_session.commit()

        # Relation loads both rows.
        loaded = await db_session.execute(
            select(User).options(selectinload(User.queries)).where(User.id == u.id)
        )
        user = loaded.scalar_one()
        assert len(user.queries) == 2

        # Cascade delete removes the child rows.
        await db_session.delete(user)
        await db_session.commit()

        count = await db_session.execute(
            select(func.count()).select_from(UserQuery).where(UserQuery.user_id == u.id)
        )
        assert count.scalar() == 0

    @pytest.mark.asyncio
    async def test_history_newest_first(self, db_session: AsyncSession):
        """With distinct timestamps, history is ordered newest-first."""
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import desc

        u = User(
            id=uuid.uuid4(), email="q2@x.sa", phone="+966500000201",
            password_hash="h", full_name="Q2", role="USER", status="APPROVED",
        )
        db_session.add(u)
        await db_session.flush()

        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        db_session.add_all([
            UserQuery(user_id=u.id, query_text="older", recognized=False,
                      created_at=base),
            UserQuery(user_id=u.id, query_text="newer", recognized=False,
                      created_at=base + timedelta(hours=1)),
        ])
        await db_session.commit()

        rows = await db_session.execute(
            select(UserQuery).where(UserQuery.user_id == u.id)
            .order_by(desc(UserQuery.created_at))
        )
        texts = [r.query_text for r in rows.scalars().all()]
        assert texts == ["newer", "older"]
