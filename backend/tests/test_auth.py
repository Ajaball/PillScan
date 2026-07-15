"""
PillScan — Authentication API Tests
=====================================

Tests for: POST /api/v1/auth/register, /auth/login, /auth/refresh
Covers: successful flows, validation errors, duplicate emails, wrong passwords.
"""

import pytest
from httpx import AsyncClient


# ══════════════════════════════════════════════════════════════════════════
# Registration Tests
# ══════════════════════════════════════════════════════════════════════════

class TestRegistration:
    """Tests for POST /api/v1/auth/register"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """A valid registration should return 201 and create a PENDING account."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@pillscan.sa",
            "password": "Secure@123",
            "full_name": "أحمد بن عبدالله",
            "phone": "+966501112233",
            "language": "ar",
        })
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["email"] == "newuser@pillscan.sa"
        assert data["status"] == "PENDING"  # Awaiting admin approval
        assert "password" not in data  # Password must never be returned
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_pending_cannot_login(self, client: AsyncClient):
        """A freshly registered (PENDING) account must not be able to log in."""
        await client.post("/api/v1/auth/register", json={
            "email": "pending@pillscan.sa",
            "password": "Secure@123",
            "full_name": "مستخدم معلق",
            "phone": "+966501119999",
            "language": "ar",
        })
        response = await client.post("/api/v1/auth/login", json={
            "email": "pending@pillscan.sa",
            "password": "Secure@123",
        })
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Registering with an existing email should fail with 409 or 400."""
        payload = {
            "email": "duplicate@pillscan.sa",
            "password": "Secure@123",
            "full_name": "مستخدم أول",
            "phone": "+966502223344",
            "language": "ar",
        }
        # First registration
        await client.post("/api/v1/auth/register", json=payload)
        # Second registration with same email (different phone)
        payload2 = {**payload, "phone": "+966502223355"}
        response = await client.post("/api/v1/auth/register", json=payload2)
        assert response.status_code in (400, 409)

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """Missing required fields should return 422 (Validation Error)."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "incomplete@pillscan.sa",
            # Missing password, full_name and phone
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_phone(self, client: AsyncClient):
        """Phone is now required at sign-up — omitting it should return 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "nophone@pillscan.sa",
            "password": "Secure@123",
            "full_name": "بدون جوال",
            "language": "ar",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Invalid email format should fail validation."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Secure@123",
            "full_name": "مستخدم خطأ",
            "phone": "+966503334455",
        })
        assert response.status_code == 422


# ══════════════════════════════════════════════════════════════════════════
# Login Tests
# ══════════════════════════════════════════════════════════════════════════

class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Valid credentials should return access and refresh tokens."""
        response = await client.post("/api/v1/auth/login", data={
            "username": test_user["email"],
            "password": test_user["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Wrong password should return 401."""
        response = await client.post("/api/v1/auth/login", data={
            "username": test_user["email"],
            "password": "WrongPassword!",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with non-existent email should return 401."""
        response = await client.post("/api/v1/auth/login", data={
            "username": "ghost@pillscan.sa",
            "password": "SomePassword",
        })
        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════════════════
# Protected Endpoint Tests
# ══════════════════════════════════════════════════════════════════════════

class TestProtectedAccess:
    """Tests for JWT-protected endpoints."""

    @pytest.mark.asyncio
    async def test_access_profile_authenticated(self, client: AsyncClient, test_user: dict):
        """Authenticated user should be able to access their profile."""
        response = await client.get(
            "/api/v1/users/me",
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]

    @pytest.mark.asyncio
    async def test_access_profile_no_token(self, client: AsyncClient):
        """No token should return 401 or 403."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_access_profile_invalid_token(self, client: AsyncClient):
        """Invalid JWT token should return 401."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code in (401, 403)
