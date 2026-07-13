"""
PillScan — Leaflet Summarizer API Tests
=========================================

Tests for: POST /api/v1/leaflet/summarize
Covers: validation, auth, the "not configured" fallback, a successful
summary with a mocked vision LLM, and provider-error handling.

The vision LLM provider call is always mocked — no network is used.
"""

import pytest
from httpx import AsyncClient

from app.services import leaflet_service


# A tiny valid JPEG magic-number prefix is enough — the router does not decode
# the image, it just forwards the bytes to the (mocked) provider.
FAKE_IMAGE = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


class TestLeafletSummarize:
    """Tests for POST /api/v1/leaflet/summarize"""

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        """Missing auth should be rejected."""
        response = await client.post(
            "/api/v1/leaflet/summarize",
            files={"image": ("leaflet.jpg", FAKE_IMAGE, "image/jpeg")},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_no_file(self, client: AsyncClient, test_user: dict):
        """Request without a file should be a validation error."""
        response = await client.post(
            "/api/v1/leaflet/summarize",
            headers=test_user["auth_header"],
        )
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_invalid_image_type(self, client: AsyncClient, test_user: dict):
        """A non-image content type should return 400."""
        response = await client.post(
            "/api/v1/leaflet/summarize",
            headers=test_user["auth_header"],
            files={"image": ("notes.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_not_configured_fallback(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """With no API key set, the endpoint returns a setup hint, not an error."""
        for attr in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3",
                     "GEMINI_API_KEY_4", "GEMINI_API_KEY_5"):
            monkeypatch.setattr(leaflet_service.settings, attr, None)

        response = await client.post(
            "/api/v1/leaflet/summarize",
            headers=test_user["auth_header"],
            files={"image": ("leaflet.jpg", FAKE_IMAGE, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
        assert data["provider"] == "gemini"
        assert "Gemini" in data["summary"]  # setup hint points to the AI settings
        assert data["disclaimer_ar"]
        assert data["disclaimer_en"]

    @pytest.mark.asyncio
    async def test_summarizes_with_mocked_gemini(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """A configured Gemini provider returns the model's Arabic summary."""
        monkeypatch.setattr(leaflet_service.settings, "GEMINI_API_KEY", "test-key")

        captured = {}

        async def fake_gemini(image_b64, mime_type, api_key, model):
            captured["b64"] = image_b64
            captured["mime"] = mime_type
            captured["api_key"] = api_key
            return "• اسم الدواء: بنادول\n• الاستخدام: مسكن للألم وخافض للحرارة"

        monkeypatch.setattr(leaflet_service, "_summarize_with_gemini", fake_gemini)

        response = await client.post(
            "/api/v1/leaflet/summarize",
            headers=test_user["auth_header"],
            files={"image": ("leaflet.jpg", FAKE_IMAGE, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is True
        assert data["provider"] == "gemini"
        assert "بنادول" in data["summary"]
        # The image was base64-encoded and forwarded with its mime type.
        assert captured["b64"]
        assert captured["mime"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_provider_error_returns_502(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """A provider failure surfaces as 502, not a 500."""
        monkeypatch.setattr(leaflet_service.settings, "GEMINI_API_KEY", "test-key")

        async def boom(image_b64, mime_type, api_key, model):
            raise leaflet_service.LeafletServiceError("upstream failed")

        monkeypatch.setattr(leaflet_service, "_summarize_with_gemini", boom)

        response = await client.post(
            "/api/v1/leaflet/summarize",
            headers=test_user["auth_header"],
            files={"image": ("leaflet.jpg", FAKE_IMAGE, "image/jpeg")},
        )
        assert response.status_code == 502


class TestLeafletServiceUnit:
    """Unit tests for the Gemini response parsing (mocked HTTP)."""

    @pytest.mark.asyncio
    async def test_gemini_parsing(self, monkeypatch):
        """The Gemini caller extracts text from a well-formed response."""
        monkeypatch.setattr(leaflet_service.settings, "GEMINI_API_KEY", "test-key")

        class FakeResponse:
            status_code = 200

            def json(self):
                return {
                    "candidates": [
                        {"content": {"parts": [{"text": "ملخّص تجريبي"}]}}
                    ]
                }

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            async def post(self, *a, **k):
                return FakeResponse()

        monkeypatch.setattr(leaflet_service.httpx, "AsyncClient", FakeClient)

        result = await leaflet_service.summarize_leaflet(FAKE_IMAGE, "image/png")
        assert result["is_configured"] is True
        assert result["summary"] == "ملخّص تجريبي"
        assert result["provider"] == "gemini"
