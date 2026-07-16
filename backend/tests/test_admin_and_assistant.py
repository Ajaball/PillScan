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
        db_session.add(
            Reminder(user_id=admin_id, medication_id=med_active.id,
                     reminder_time=time(8, 0), is_active=True)
        )
        await db_session.commit()

        response = await client.get(
            "/api/v1/admin/stats", headers=admin_user["auth_header"],
        )
        data = response.json()
        assert data["scans"] == 2
        assert data["medications"] == 1  # only the active medication is counted
        assert data["reminders"] == 1
        assert data["queries"] == 1


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
        # Fixed three-field contract is always present, in order.
        assert list(data.keys())[:3] == ["name", "sideEffects", "usageTimes"]
        assert data["sideEffects"] == []
        assert data["usageTimes"] == []
        assert data["message"]  # a setup hint is provided

    @pytest.mark.asyncio
    async def test_assistant_returns_three_fields_in_order(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """With a (mocked) model reply, the endpoint returns exactly the 3 fields."""
        # Give the user a key so resolution is non-empty.
        await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "TEST-KEY"},
        )

        async def fake_ask(drug_name, api_key, model):
            return json.dumps({
                "name": "بنادول",
                "sideEffects": ["غثيان", "طفح جلدي نادر"],
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
        assert list(data.keys())[:3] == ["name", "sideEffects", "usageTimes"]
        assert data["name"] == "بنادول"
        assert data["sideEffects"] == ["غثيان", "طفح جلدي نادر"]
        assert data["usageTimes"] == ["صباحًا", "مساءً بعد الأكل"]
        # Removed fields must not be present.
        assert "dosage" not in data
        assert "contraindications" not in data
