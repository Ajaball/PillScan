"""
Regression tests for bugs found in the Phase-1 audit:

1. Async lazy-load of relationships in medications/reminders routers → 500.
2. Adherence calendar accepts an invalid month (e.g. 2026-13) → 500.
3. (Frontend days_of_week bug is fixed in reminders.js; covered by manual check.)

These fail (500) before the fix and pass (200/422) after it.
"""

import uuid
from datetime import time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drug import Drug
from app.models.medication import Medication
from app.models.reminder import Reminder


@pytest.fixture
def drug_id():
    return uuid.uuid4()


@pytest.fixture
def med_id():
    return uuid.uuid4()


@pytest.mark.asyncio
async def test_list_medications_with_drug_link(
    client: AsyncClient, test_user: dict, db_session: AsyncSession
):
    """A drug-linked medication must list without a lazy-load 500."""
    d_id = uuid.uuid4()
    db_session.add(Drug(
        id=d_id, name_en="Panadol", name_ar="بانادول",
        generic_name_en="Paracetamol", dosage_form="tablet",
        strength="500mg", is_active=True,
    ))
    db_session.add(Medication(
        id=uuid.uuid4(), user_id=uuid.UUID(test_user["id"]), drug_id=d_id,
        dosage="1 tablet", frequency="daily", is_active=True,
    ))
    await db_session.commit()

    r = await client.get("/api/v1/medications/", headers=test_user["auth_header"])
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["drug_name_en"] == "Panadol"


@pytest.mark.asyncio
async def test_list_reminders_with_drug_linked_medication(
    client: AsyncClient, test_user: dict, db_session: AsyncSession
):
    """Listing reminders whose medication is drug-linked must not 500."""
    d_id = uuid.uuid4()
    m_id = uuid.uuid4()
    db_session.add(Drug(
        id=d_id, name_en="Brufen", name_ar="بروفين",
        generic_name_en="Ibuprofen", dosage_form="tablet",
        strength="400mg", is_active=True,
    ))
    db_session.add(Medication(
        id=m_id, user_id=uuid.UUID(test_user["id"]), drug_id=d_id,
        frequency="daily", is_active=True,
    ))
    db_session.add(Reminder(
        id=uuid.uuid4(), user_id=uuid.UUID(test_user["id"]), medication_id=m_id,
        reminder_time=time(8, 0), days_of_week=[0, 1, 2], is_active=True,
    ))
    await db_session.commit()

    r = await client.get("/api/v1/reminders/", headers=test_user["auth_header"])
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["medication_name"] == "Brufen"  # from drug via lazy-safe load


@pytest.mark.asyncio
async def test_calendar_rejects_invalid_month(client: AsyncClient, test_user: dict):
    """An out-of-range month must be a 4xx, not a 500 from datetime()."""
    r = await client.get(
        "/api/v1/adherence/calendar?month=2026-13", headers=test_user["auth_header"],
    )
    assert r.status_code in (400, 422)


@pytest.mark.asyncio
async def test_calendar_accepts_valid_month(client: AsyncClient, test_user: dict):
    r = await client.get(
        "/api/v1/adherence/calendar?month=2026-07", headers=test_user["auth_header"],
    )
    assert r.status_code == 200
