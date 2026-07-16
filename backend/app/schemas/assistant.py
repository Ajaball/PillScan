"""
Pharmacist Assistant Schemas
Request/response models for the AI drug-information assistant endpoint.
"""

from typing import List
from pydantic import BaseModel, Field


class DrugInfoRequest(BaseModel):
    """A drug name to look up (Arabic or English)."""
    name: str = Field(..., min_length=1, max_length=120)


class DrugInfoResponse(BaseModel):
    """
    Fixed-shape drug information returned by the assistant. The three display
    fields are ALWAYS present and ALWAYS in this order:
        1. name        — اسم الدواء
        2. sideEffects — الأعراض الجانبية
        3. usageTimes  — مواعيد الاستخدام

    ``recognized`` is False when the model does not confidently recognise the
    drug (client shows a clear "not recognised" message instead of fabricated
    content). ``is_configured`` is False when no Gemini key is set. ``message``
    carries a status/error note and is not one of the three display fields.
    """
    name: str = ""                          # اسم الدواء
    sideEffects: List[str] = []             # الأعراض الجانبية
    usageTimes: List[str] = []              # مواعيد الاستخدام
    recognized: bool = False

    provider: str = "gemini"
    model: str = ""
    is_configured: bool = True
    disclaimer_ar: str = ""
    message: str = ""
