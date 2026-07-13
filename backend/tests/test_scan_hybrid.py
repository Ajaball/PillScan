"""
PillScan — Hybrid Scan Tests
=============================

Tests for POST /api/v1/scan/identify covering the hybrid identification
strategy: CV model first, vision-LLM fallback, and an honest "unidentified"
result when neither identifies the pill.

Key regression guard: an unidentified scan must NOT fabricate a confident
"Panadol Extra" match (the old demo-fallback behaviour).

The CV model and the LLM provider are mocked — no network or ONNX is used.
"""

import io
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image as PILImage

from app.routers import scan as scan_router
from app.services import pill_id_service


def _jpeg_bytes(color=(200, 100, 50)) -> bytes:
    """Create a small, valid JPEG so the router can read its dimensions."""
    buf = io.BytesIO()
    PILImage.new("RGB", (64, 64), color).save(buf, format="JPEG")
    return buf.getvalue()


class TestHybridScan:
    """Tests for the CV → LLM → honest-empty identification chain."""

    @pytest_asyncio.fixture(autouse=True)
    async def seed_drugs(self, db_session: AsyncSession):
        from app.models.drug import Drug

        db_session.add_all([
            Drug(
                id=uuid.uuid4(),
                name_en="Panadol Extra", name_ar="بانادول إكسترا",
                generic_name_en="Paracetamol + Caffeine",
                dosage_form="tablet", strength="500mg", is_active=True,
            ),
            Drug(
                id=uuid.uuid4(),
                name_en="Brufen 400mg", name_ar="بروفين",
                generic_name_en="Ibuprofen", generic_name_ar="ايبوبروفين",
                dosage_form="tablet", strength="400mg", is_active=True,
            ),
        ])
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_llm_fallback_maps_to_db(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """When CV is off, the LLM candidate is mapped to the DB drug."""
        monkeypatch.setattr(scan_router.settings, "SCAN_AI_MODEL_ENABLED", False)

        async def fake_identify(image_bytes, content_type, user=None):
            return {
                "provider": "gemini", "model": "g",
                "candidates": [{
                    "name_en": "Brufen", "name_ar": "بروفين",
                    "generic_en": "Ibuprofen", "strength": "400mg",
                    "dosage_form": "tablet", "confidence": 0.91,
                }],
            }

        monkeypatch.setattr(pill_id_service, "identify_pill", fake_identify)

        response = await client.post(
            "/api/v1/scan/identify",
            headers=test_user["auth_header"],
            files={"image": ("pill.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inference_mode"] == "llm"
        assert len(data["predictions"]) == 1
        pred = data["predictions"][0]
        assert pred["drug_id"] is not None
        assert "Brufen" in pred["drug_name_en"]

    @pytest.mark.asyncio
    async def test_llm_unmatched_candidate_still_surfaced(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """An LLM identification not in the DB is still returned (drug_id null)."""
        monkeypatch.setattr(scan_router.settings, "SCAN_AI_MODEL_ENABLED", False)

        async def fake_identify(image_bytes, content_type, user=None):
            return {
                "provider": "gemini", "model": "g",
                "candidates": [{
                    "name_en": "Zappix", "name_ar": "زابيكس",
                    "generic_en": "Unobtainium", "strength": "10mg",
                    "dosage_form": "capsule", "confidence": 0.6,
                }],
            }

        monkeypatch.setattr(pill_id_service, "identify_pill", fake_identify)

        response = await client.post(
            "/api/v1/scan/identify",
            headers=test_user["auth_header"],
            files={"image": ("pill.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inference_mode"] == "llm"
        pred = data["predictions"][0]
        assert pred["drug_id"] is None
        assert pred["drug_name_en"] == "Zappix"

    @pytest.mark.asyncio
    async def test_unidentified_is_honest_not_panadol(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """
        Regression: when nothing identifies the pill, the result is an empty
        list with mode 'unidentified' — NOT a fabricated Panadol match.
        """
        monkeypatch.setattr(scan_router.settings, "SCAN_AI_MODEL_ENABLED", False)

        async def fake_identify(image_bytes, content_type, user=None):
            return None  # provider not configured

        monkeypatch.setattr(pill_id_service, "identify_pill", fake_identify)

        response = await client.post(
            "/api/v1/scan/identify",
            headers=test_user["auth_header"],
            files={"image": ("pill.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inference_mode"] == "unidentified"
        assert data["predictions"] == []

    @pytest.mark.asyncio
    async def test_llm_error_degrades_to_unidentified(
        self, client: AsyncClient, test_user: dict, monkeypatch
    ):
        """A provider error during fallback yields an honest empty result."""
        monkeypatch.setattr(scan_router.settings, "SCAN_AI_MODEL_ENABLED", False)

        async def boom(image_bytes, content_type, user=None):
            raise pill_id_service.PillIdError("provider down")

        monkeypatch.setattr(pill_id_service, "identify_pill", boom)

        response = await client.post(
            "/api/v1/scan/identify",
            headers=test_user["auth_header"],
            files={"image": ("pill.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inference_mode"] == "unidentified"
        assert data["predictions"] == []
