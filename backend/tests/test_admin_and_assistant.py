"""
PillScan — Admin approval workflow & assistant guard tests
==========================================================

Covers the end-to-end approval flow (register PENDING → cannot log in → admin
approves → can log in), server-side admin role enforcement, and the assistant
endpoint's approved-user guard.
"""

import json
import pytest
from httpx import AsyncClient

from app.services import assistant_service


class TestAdminApprovalFlow:
    @pytest.mark.asyncio
    async def test_full_approval_flow(self, client: AsyncClient, admin_user: dict):
        # 1) Register a new user → PENDING
        reg = await client.post("/api/v1/auth/register", json={
            "email": "flow@pillscan.sa",
            "password": "Secure@123",
            "full_name": "مستخدم تدفق",
            "phone": "+966505550001",
            "language": "ar",
        })
        assert reg.status_code in (200, 201)
        assert reg.json()["status"] == "PENDING"
        user_id = reg.json()["id"]

        # 2) PENDING account cannot log in
        login1 = await client.post("/api/v1/auth/login", json={
            "email": "flow@pillscan.sa", "password": "Secure@123",
        })
        assert login1.status_code == 403

        # 3) Admin sees it in the pending list
        pending = await client.get(
            "/api/v1/admin/users?status=PENDING", headers=admin_user["auth_header"],
        )
        assert pending.status_code == 200
        assert any(u["id"] == user_id for u in pending.json())

        # 4) Admin approves
        approve = await client.patch(
            f"/api/v1/admin/users/{user_id}/status",
            json={"status": "APPROVED"},
            headers=admin_user["auth_header"],
        )
        assert approve.status_code == 200
        assert approve.json()["status"] == "APPROVED"

        # 5) Now the user can log in
        login2 = await client.post("/api/v1/auth/login", json={
            "email": "flow@pillscan.sa", "password": "Secure@123",
        })
        assert login2.status_code == 200
        assert "access_token" in login2.json()

    @pytest.mark.asyncio
    async def test_rejected_cannot_login(self, client: AsyncClient, admin_user: dict):
        reg = await client.post("/api/v1/auth/register", json={
            "email": "reject@pillscan.sa",
            "password": "Secure@123",
            "full_name": "مرفوض",
            "phone": "+966505550002",
            "language": "ar",
        })
        user_id = reg.json()["id"]
        await client.patch(
            f"/api/v1/admin/users/{user_id}/status",
            json={"status": "REJECTED"},
            headers=admin_user["auth_header"],
        )
        login = await client.post("/api/v1/auth/login", json={
            "email": "reject@pillscan.sa", "password": "Secure@123",
        })
        assert login.status_code == 403


class TestAdminAccessControl:
    @pytest.mark.asyncio
    async def test_non_admin_cannot_list_users(self, client: AsyncClient, test_user: dict):
        """A regular (approved) user must be rejected by the server, not just UI."""
        response = await client.get(
            "/api/v1/admin/users", headers=test_user["auth_header"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_non_admin_cannot_change_status(self, client: AsyncClient, test_user: dict):
        response = await client.patch(
            f"/api/v1/admin/users/{test_user['id']}/status",
            json={"status": "REJECTED"},
            headers=test_user["auth_header"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_list_all_users(self, client: AsyncClient, admin_user: dict):
        response = await client.get(
            "/api/v1/admin/users", headers=admin_user["auth_header"],
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_db_status_admin_only(self, client: AsyncClient, test_user: dict):
        response = await client.get(
            "/api/v1/admin/db-status", headers=test_user["auth_header"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_db_status_reports_engine(self, client: AsyncClient, admin_user: dict):
        response = await client.get(
            "/api/v1/admin/db-status", headers=admin_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["engine"] in ("sqlite", "postgres")
        assert "persistent" in data

    @pytest.mark.asyncio
    async def test_stats_admin_only(self, client: AsyncClient, test_user: dict):
        """Activity stats are admin-only — a regular user is rejected server-side."""
        response = await client.get(
            "/api/v1/admin/stats", headers=test_user["auth_header"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_stats_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/admin/stats")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_stats_returns_all_counters(self, client: AsyncClient, admin_user: dict):
        """The endpoint returns every expected counter as a non-negative integer."""
        response = await client.get(
            "/api/v1/admin/stats", headers=admin_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        for key in ("scans", "medications", "reminders", "queries"):
            assert key in data
            assert isinstance(data[key], int)
            assert data[key] >= 0
        # 7-day scan trend: always exactly 7 ordered {date, count} buckets.
        assert isinstance(data["scan_trend"], list)
        assert len(data["scan_trend"]) == 7
        for bucket in data["scan_trend"]:
            assert set(bucket.keys()) == {"date", "count"}
            assert isinstance(data["scan_trend"][0]["count"], int)
        dates = [b["date"] for b in data["scan_trend"]]
        assert dates == sorted(dates)  # chronological order

    @pytest.mark.asyncio
    async def test_stats_reflects_created_rows(
        self, client: AsyncClient, admin_user: dict, db_session
    ):
        """Counters increase when matching rows exist, and honor the is_active filter."""
        import uuid
        from datetime import time
        from app.models.scan_history import ScanHistory
        from app.models.medication import Medication
        from app.models.reminder import Reminder
        from app.models.user_query import UserQuery

        admin_id = uuid.UUID(admin_user["id"])

        med_active = Medication(user_id=admin_id, drug_id=None, is_active=True)
        med_inactive = Medication(user_id=admin_id, drug_id=None, is_active=False)
        db_session.add_all([
            ScanHistory(user_id=admin_id, image_url="http://x/a.jpg"),
            ScanHistory(user_id=admin_id, image_url="http://x/b.jpg"),
            med_active,
            med_inactive,
            UserQuery(user_id=admin_id, query_text="بنادول", recognized=True),
        ])
        await db_session.flush()
        # One active + one inactive reminder so the count truly proves the
        # is_active filter (a count of 1 fails if the predicate is dropped).
        db_session.add_all([
            Reminder(user_id=admin_id, medication_id=med_active.id,
                     reminder_time=time(8, 0), is_active=True),
            Reminder(user_id=admin_id, medication_id=med_active.id,
                     reminder_time=time(20, 0), is_active=False),
        ])
        await db_session.commit()

        response = await client.get(
            "/api/v1/admin/stats", headers=admin_user["auth_header"],
        )
        data = response.json()
        assert data["scans"] == 2
        assert data["medications"] == 1  # only the active medication is counted
        assert data["reminders"] == 1  # only the active reminder is counted
        assert data["queries"] == 1
        # Both scans were created "now", so today's bucket (the last one) holds
        # them and the 7-day trend sums to the total scan count.
        assert sum(b["count"] for b in data["scan_trend"]) == 2
        assert data["scan_trend"][-1]["count"] == 2

    @pytest.mark.asyncio
    async def test_query_stats_admin_only(self, client: AsyncClient, test_user: dict):
        response = await client.get(
            "/api/v1/admin/query-stats", headers=test_user["auth_header"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_query_stats_empty(self, client: AsyncClient, admin_user: dict):
        """With no queries, the per-user breakdown is an empty list, not an error."""
        response = await client.get(
            "/api/v1/admin/query-stats", headers=admin_user["auth_header"],
        )
        assert response.status_code == 200
        assert response.json()["users"] == []

    @pytest.mark.asyncio
    async def test_query_stats_per_user_breakdown(
        self, client: AsyncClient, admin_user: dict, test_user: dict, db_session
    ):
        """Per-user counts, recognized sub-count, and most-active-first ordering."""
        import uuid
        from app.models.user_query import UserQuery

        admin_id = uuid.UUID(admin_user["id"])
        user_id = uuid.UUID(test_user["id"])
        db_session.add_all([
            UserQuery(user_id=admin_id, query_text="بنادول", recognized=True),
            UserQuery(user_id=admin_id, query_text="اسبرين", recognized=True),
            UserQuery(user_id=admin_id, query_text="xyz", recognized=False),
            UserQuery(user_id=user_id, query_text="فيتامين", recognized=True),
        ])
        await db_session.commit()

        response = await client.get(
            "/api/v1/admin/query-stats", headers=admin_user["auth_header"],
        )
        assert response.status_code == 200
        users = response.json()["users"]
        # Only users with queries appear (both admin and the regular user).
        assert len(users) == 2
        # Ordered by total desc: admin (3 queries) before the regular user (1).
        assert users[0]["user_id"] == str(admin_id)
        assert users[0]["total"] == 3
        # recognized sub-count proves the case() sum works (2 of 3 recognized),
        # not just a copy of total — a false green would show 3 here.
        assert users[0]["recognized"] == 2
        assert users[0]["last_at"] is not None
        assert set(users[0].keys()) == {
            "user_id", "full_name", "email", "total", "recognized", "last_at",
        }
        assert users[1]["user_id"] == str(user_id)
        assert users[1]["total"] == 1
        assert users[1]["recognized"] == 1

    @pytest.mark.asyncio
    async def test_user_queries_admin_only(self, client: AsyncClient, test_user: dict):
        response = await client.get(
            f"/api/v1/admin/users/{test_user['id']}/queries",
            headers=test_user["auth_header"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_user_queries_detail(
        self, client: AsyncClient, admin_user: dict, test_user: dict, db_session
    ):
        """One user's individual queries: newest first, with recognized name."""
        import uuid
        from app.models.user_query import UserQuery

        user_id = uuid.UUID(test_user["id"])
        admin_id = uuid.UUID(admin_user["id"])
        # Explicit, distinct timestamps so the newest-first ordering is genuinely
        # testable. (SQLite's func.now() has 1s resolution, so two rows in one
        # transaction would otherwise share a timestamp and make the ordering
        # assertion vacuous — passing even if the endpoint sorted ascending.)
        from datetime import datetime
        older = datetime(2026, 1, 1, 10, 0, 0)
        newer = datetime(2026, 1, 1, 10, 5, 0)
        db_session.add_all([
            UserQuery(user_id=user_id, query_text="بنادول", recognized=True,
                      result={"name": "باراسيتامول"}, created_at=older),
            UserQuery(user_id=user_id, query_text="زبالة", recognized=False,
                      result=None, created_at=newer),
            # Belongs to a different user — must NOT leak into this response.
            UserQuery(user_id=admin_id, query_text="اسبرين", recognized=True),
        ])
        await db_session.commit()

        response = await client.get(
            f"/api/v1/admin/users/{test_user['id']}/queries",
            headers=admin_user["auth_header"],
        )
        assert response.status_code == 200
        queries = response.json()["queries"]
        # Only this user's two queries, never the admin's.
        assert len(queries) == 2
        texts = {q["query_text"] for q in queries}
        assert texts == {"بنادول", "زبالة"}
        # Newest first: "زبالة" (newer) must come before "بنادول" (older).
        # Distinct timestamps make this fail if the endpoint sorts ascending.
        assert [q["query_text"] for q in queries] == ["زبالة", "بنادول"]
        # Shape + recognized_name resolution.
        recognized = next(q for q in queries if q["query_text"] == "بنادول")
        assert recognized["recognized"] is True
        assert recognized["recognized_name"] == "باراسيتامول"
        not_recognized = next(q for q in queries if q["query_text"] == "زبالة")
        assert not_recognized["recognized"] is False
        assert not_recognized["recognized_name"] is None
        assert set(recognized.keys()) == {
            "id", "query_text", "recognized", "recognized_name", "created_at",
        }

    @pytest.mark.asyncio
    async def test_user_queries_empty_for_unknown_user(
        self, client: AsyncClient, admin_user: dict
    ):
        """An admin querying a user with no history gets an empty list, not an error."""
        import uuid
        response = await client.get(
            f"/api/v1/admin/users/{uuid.uuid4()}/queries",
            headers=admin_user["auth_header"],
        )
        assert response.status_code == 200
        assert response.json()["queries"] == []


class TestAssistantGuard:
    @pytest.mark.asyncio
    async def test_assistant_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/assistant/drug-info", json={"name": "Panadol"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_assistant_no_key_returns_not_recognized(
        self, client: AsyncClient, test_user: dict
    ):
        """With no Gemini key configured the endpoint degrades gracefully."""
        response = await client.post(
            "/api/v1/assistant/drug-info",
            json={"name": "Panadol"},
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
        assert data["recognized"] is False
        # Comprehensive contract: all display fields present (empty when unknown).
        for field in ("name", "activeIngredient", "uses", "dosage",
                      "sideEffects", "warnings", "contraindications", "usageTimes"):
            assert field in data
        assert data["sideEffects"] == []
        assert data["usageTimes"] == []
        assert data["message"]  # a setup hint is provided

    @pytest.mark.asyncio
    async def test_assistant_returns_comprehensive_fields(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """With a (mocked) model reply, the endpoint returns the full drug profile."""
        # Give the user a key so resolution is non-empty.
        await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "TEST-KEY"},
        )

        async def fake_ask(drug_name, api_key, model):
            return json.dumps({
                "name": "بنادول",
                "activeIngredient": "باراسيتامول",
                "uses": ["خفض الحرارة", "تسكين الألم"],
                "dosage": ["قرص كل 6 ساعات"],
                "sideEffects": ["غثيان", "طفح جلدي نادر"],
                "warnings": ["لا تتجاوز 4 جرام يوميًا"],
                "contraindications": ["فشل كبدي شديد"],
                "usageTimes": ["صباحًا", "مساءً بعد الأكل"],
                "recognized": True,
            })

        monkeypatch.setattr(assistant_service, "_ask_gemini", fake_ask)

        r = await client.post(
            "/api/v1/assistant/drug-info",
            headers=test_user["auth_header"],
            json={"name": "Panadol"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["recognized"] is True
        assert data["name"] == "بنادول"
        assert data["activeIngredient"] == "باراسيتامول"
        assert data["uses"] == ["خفض الحرارة", "تسكين الألم"]
        assert data["dosage"] == ["قرص كل 6 ساعات"]
        assert data["sideEffects"] == ["غثيان", "طفح جلدي نادر"]
        assert data["warnings"] == ["لا تتجاوز 4 جرام يوميًا"]
        assert data["contraindications"] == ["فشل كبدي شديد"]
        assert data["usageTimes"] == ["صباحًا", "مساءً بعد الأكل"]
