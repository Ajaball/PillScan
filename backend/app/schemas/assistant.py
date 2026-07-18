"""
Pharmacist Assistant Schemas
Request/response models for the AI drug-information assistant endpoint.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class DrugInfoRequest(BaseModel):
    """A drug name to look up (Arabic or English)."""
    name: str = Field(..., min_length=1, max_length=120)


class DrugQueryHistoryItem(BaseModel):
    """One past drug-assistant lookup from the user's query history."""
    id: UUID
    query_text: str
    recognized: bool
    result: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DrugInfoResponse(BaseModel):
    """
    Comprehensive drug information returned by the assistant. All display fields
    are ALWAYS present (empty when unknown) so the client can render whatever the
    model provided:
        name              — اسم الدواء
        activeIngredient  — المادة الفعّالة
        uses              — دواعي الاستعمال
        dosage            — الجرعة المعتادة
        sideEffects       — الأعراض الجانبية
        warnings          — تحذيرات واحتياطات
        contraindications — موانع الاستعمال
        usageTimes        — مواعيد الاستخدام

    ``recognized`` is False only when the model does not recognise the drug at
    all (client shows a clear "not recognised" message instead of fabricated
    content). ``is_configured`` is False when no Gemini key is set. ``message``
    carries a status/error note and is not a display field.
    """
    name: str = ""                          # اسم الدواء
    activeIngredient: str = ""              # المادة الفعّالة
    uses: List[str] = []                    # دواعي الاستعمال
    dosage: List[str] = []                  # الجرعة المعتادة
    sideEffects: List[str] = []             # الأعراض الجانبية
    warnings: List[str] = []                # تحذيرات واحتياطات
    contraindications: List[str] = []       # موانع الاستعمال
    usageTimes: List[str] = []              # مواعيد الاستخدام
    recognized: bool = False

    provider: str = "gemini"
    model: str = ""
    is_configured: bool = True
    disclaimer_ar: str = ""
    message: str = ""
