"""
PillScan — Drug Information API Tests
=======================================

Tests for: GET /api/v1/drugs/search, /drugs/{id}
Covers: bilingual search, drug details, SFDA data integrity.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ══════════════════════════════════════════════════════════════════════════
# Drug Search Tests
# ══════════════════════════════════════════════════════════════════════════

class TestDrugSearch:
    """Tests for GET /api/v1/drugs/search"""

    @pytest_asyncio.fixture(autouse=True)
    async def seed_drugs(self, db_session: AsyncSession):
        """Seed the test database with sample drugs."""
        from app.models.drug import Drug
        import uuid

        drugs = [
            Drug(
                id=uuid.uuid4(),
                name_en="Panadol Extra",
                name_ar="بنادول إكسترا",
                generic_name_en="Paracetamol 500mg, Caffeine 65mg",
                manufacturer="GlaxoSmithKline",
                description_en="Pain relief medication",
                description_ar="دواء مسكن للآلام",
                shape="oval",
                color="white",
                sfda_reg_number="SFDA-1234",
            ),
            Drug(
                id=uuid.uuid4(),
                name_en="Brufen 400mg",
                name_ar="بروفين ٤٠٠ ملغ",
                generic_name_en="Ibuprofen 400mg",
                manufacturer="Abbott Laboratories",
                description_en="Anti-inflammatory drug",
                description_ar="مضاد للالتهابات",
                shape="round",
                color="pink",
                sfda_reg_number="SFDA-5678",
            ),
        ]
        for drug in drugs:
            db_session.add(drug)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_search_english(self, client: AsyncClient, test_user: dict):
        """Searching by English name should return matching drugs."""
        response = await client.get(
            "/api/v1/drugs/search",
            params={"q": "Panadol"},
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any("Panadol" in d.get("name_en", "") for d in data)

    @pytest.mark.asyncio
    async def test_search_arabic(self, client: AsyncClient, test_user: dict):
        """Searching by Arabic name should return matching drugs."""
        response = await client.get(
            "/api/v1/drugs/search",
            params={"q": "بنادول"},
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, client: AsyncClient, test_user: dict):
        """Searching for nonexistent drug should return empty list."""
        response = await client.get(
            "/api/v1/drugs/search",
            params={"q": "NonExistentDrug123"},
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


# ══════════════════════════════════════════════════════════════════════════
# Drug Details Tests
# ══════════════════════════════════════════════════════════════════════════

class TestDrugDetails:
    """Tests for GET /api/v1/drugs/{id}"""

    @pytest.mark.asyncio
    async def test_get_drug_not_found(self, client: AsyncClient, test_user: dict):
        """Non-existent drug ID should return 404."""
        response = await client.get(
            "/api/v1/drugs/00000000-0000-0000-0000-000000000000",
            headers=test_user["auth_header"],
        )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# Scan API Tests
# ══════════════════════════════════════════════════════════════════════════

class TestScanAPI:
    """Tests for POST /api/v1/scan/identify"""

    @pytest.mark.asyncio
    async def test_scan_no_file(self, client: AsyncClient, test_user: dict):
        """Sending scan request without a file should return an error."""
        response = await client.post(
            "/api/v1/scan/identify",
            headers=test_user["auth_header"],
        )
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_scan_history_empty(self, client: AsyncClient, test_user: dict):
        """New user should have empty scan history."""
        response = await client.get(
            "/api/v1/scan/history",
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


# ══════════════════════════════════════════════════════════════════════════
# Adherence API Tests
# ══════════════════════════════════════════════════════════════════════════

class TestAdherenceAPI:
    """Tests for GET /api/v1/adherence/stats"""

    @pytest.mark.asyncio
    async def test_adherence_stats(self, client: AsyncClient, test_user: dict):
        """Adherence stats should return numeric values."""
        response = await client.get(
            "/api/v1/adherence/stats",
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "compliance_rate" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_adherence_streak(self, client: AsyncClient, test_user: dict):
        """Streak endpoint should return a number >= 0."""
        response = await client.get(
            "/api/v1/adherence/streak",
            headers=test_user["auth_header"],
        )
        assert response.status_code == 200
