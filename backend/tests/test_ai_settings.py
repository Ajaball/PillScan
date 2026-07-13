"""
PillScan — AI Settings API Tests
=================================

Tests for the user-supplied Gemini key management used by pill identification
and the leaflet summarizer:
    GET  /api/v1/users/me/ai-settings
    PUT  /api/v1/users/me/ai-settings

Covers auth, storing/masking keys (never returned in plaintext), clearing a
key, up to five key slots, that a user's own key is preferred over the
server-wide .env key, and automatic failover to the next key.
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
        """A fresh user has five empty key slots."""
        r = await client.get("/api/v1/users/me/ai-settings", headers=test_user["auth_header"])
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "gemini"
        assert data["configured_count"] == 0
        assert len(data["keys"]) == 5
        assert all(k["configured"] is False for k in data["keys"])
        assert data["keys"][0]["slot"] == 1

    @pytest.mark.asyncio
    async def test_set_key_is_masked_and_persisted(self, client: AsyncClient, test_user: dict):
        """Saving a key returns a masked hint, never the raw value."""
        r = await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "AIzaSy-secret-KEY-9999"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["configured_count"] == 1
        assert data["keys"][0]["configured"] is True
        # The raw key must not be echoed back anywhere in the response.
        assert "AIzaSy-secret-KEY-9999" not in str(data)
        assert data["keys"][0]["hint"].endswith("9999")

        # Persisted across a fresh GET.
        r2 = await client.get("/api/v1/users/me/ai-settings", headers=test_user["auth_header"])
        assert r2.json()["keys"][0]["configured"] is True

    @pytest.mark.asyncio
    async def test_multiple_slots_and_clear(self, client: AsyncClient, test_user: dict):
        """Keys can be stored in several slots and cleared individually."""
        r = await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "KEY-ONE-1111", "gemini_api_key_3": "KEY-THREE-3333"},
        )
        data = r.json()
        assert data["configured_count"] == 2
        assert data["keys"][0]["configured"] is True
        assert data["keys"][2]["configured"] is True

        # Empty string clears just that slot.
        r2 = await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": ""},
        )
        data2 = r2.json()
        assert data2["keys"][0]["configured"] is False
        assert data2["keys"][2]["configured"] is True
        assert data2["configured_count"] == 1


class TestPerUserKeyPreferenceAndFailover:
    @pytest.mark.asyncio
    async def test_user_key_preferred_over_env(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """The user's own key is used for summarization, not the .env key."""
        monkeypatch.setattr(leaflet_service.llm_keys.settings, "GEMINI_API_KEY", "SERVER-ENV-KEY")

        await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "USER-OWN-KEY"},
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

    @pytest.mark.asyncio
    async def test_failover_to_next_key(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """When the first key fails, the next key is used automatically."""
        await client.put(
            "/api/v1/users/me/ai-settings",
            headers=test_user["auth_header"],
            json={"gemini_api_key": "DEAD-KEY", "gemini_api_key_2": "GOOD-KEY"},
        )

        used = []

        async def fake_gemini(image_b64, mime_type, api_key, model):
            used.append(api_key)
            if api_key == "DEAD-KEY":
                raise leaflet_service.LeafletServiceError("quota exhausted")
            return "ملخّص من المفتاح الثاني"

        monkeypatch.setattr(leaflet_service, "_summarize_with_gemini", fake_gemini)

        r = await client.post(
            "/api/v1/leaflet/summarize",
            headers=test_user["auth_header"],
            files={"image": ("leaflet.jpg", b"\xff\xd8\xff\xe0fake", "image/jpeg")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["is_configured"] is True
        assert "الثاني" in data["summary"]
        assert used == ["DEAD-KEY", "GOOD-KEY"]  # tried in order, failed over


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
