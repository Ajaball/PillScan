"""
PillScan — AI Settings API Tests
=================================

Tests for the user-supplied LLM API key management used by the leaflet
summarizer:
    GET  /api/v1/users/me/ai-settings
    PUT  /api/v1/users/me/ai-settings

Covers auth, storing/masking keys (never returned in plaintext), clearing a
key, provider selection, and that a user's own key is preferred over the
server-wide .env key when summarizing.
"""

import pytest
from httpx import AsyncClient

from app.services import leaflet_service
from app.utils.crypto import encrypt_secret, decrypt_secret


class TestAISettingsEndpoints:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/v1/users/me/ai-settings")).status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_defaults_empty(self, client: AsyncClient, test_user: dict):
        """A fresh user has no keys configured."""
        r = await client.get("/api/v1/users/me/ai-settings", headers=test_user["auth_header"])
        assert r.status_code == 200
        data = r.json()
        assert data["gemini_configured"] is False
        assert data["openai_configured"] is False
        assert data["gemini_key_hint"] is None
        assert data["llm_provider"] in ("gemini", "openai")

    @pytest.mark.asyncio
    async def test_set_key_is_masked_and_persisted(self, client: AsyncClient, test_user: dict):
        """Saving a key returns a masked hint, never the raw value."""
        r = await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "AIzaSy-secret-KEY-9999", "llm_provider": "gemini"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["gemini_configured"] is True
        assert data["llm_provider"] == "gemini"
        # The raw key must not be echoed back anywhere in the response.
        assert "AIzaSy-secret-KEY-9999" not in str(data)
        assert data["gemini_key_hint"].endswith("9999")

        # Persisted across a fresh GET.
        r2 = await client.get("/api/v1/users/me/ai-settings", headers=test_user["auth_header"])
        assert r2.json()["gemini_configured"] is True

    @pytest.mark.asyncio
    async def test_clear_key(self, client: AsyncClient, test_user: dict):
        await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"openai_api_key": "sk-openai-test-1234"},
        )
        # Empty string clears it.
        r = await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"openai_api_key": ""},
        )
        assert r.json()["openai_configured"] is False

    @pytest.mark.asyncio
    async def test_invalid_provider_rejected(self, client: AsyncClient, test_user: dict):
        r = await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"llm_provider": "not-a-provider"},
        )
        assert r.status_code == 422


class TestPerUserKeyPreference:
    @pytest.mark.asyncio
    async def test_user_key_preferred_over_env(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """The user's own key is used for summarization, not the .env key."""
        # Server default has a different key configured.
        monkeypatch.setattr(leaflet_service.settings, "LLM_PROVIDER", "gemini")
        monkeypatch.setattr(leaflet_service.settings, "GEMINI_API_KEY", "SERVER-ENV-KEY")

        # User saves their own Gemini key and selects Gemini.
        await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "USER-OWN-KEY", "llm_provider": "gemini"},
        )

        captured = {}

        async def fake_gemini(image_b64, mime_type, api_key, model):
            captured["api_key"] = api_key
            return "ملخّص"

        monkeypatch.setattr(leaflet_service, "_summarize_with_gemini", fake_gemini)

        r = await client.post(
            "/api/v1/leaflet/summarize",
            headers=test_user["auth_header"],
            files={"image": ("leaflet.jpg", b"\xff\xd8\xff\xe0fake", "image/jpeg")},
        )
        assert r.status_code == 200
        assert r.json()["is_configured"] is True
        assert captured["api_key"] == "USER-OWN-KEY"  # not "SERVER-ENV-KEY"


class TestCryptoUnit:
    def test_roundtrip_and_tamper(self):
        token = encrypt_secret("super-secret-value")
        assert token != "super-secret-value"
        assert decrypt_secret(token) == "super-secret-value"
        # Tampering (flipping the last chars) fails the HMAC → None.
        tampered = token[:-3] + ("AAA" if not token.endswith("AAA") else "BBB")
        assert decrypt_secret(tampered) is None

    def test_empty_values(self):
        assert encrypt_secret("") is None
        assert encrypt_secret(None) is None
        assert decrypt_secret(None) is None
        assert decrypt_secret("not-valid-base64!!") is None
