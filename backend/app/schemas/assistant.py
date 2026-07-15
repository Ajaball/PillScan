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
    Structured, general drug information returned by the assistant.

    ``recognized`` is False when the model does not confidently recognise the
    drug — the client then shows a clear "not recognised" message instead of
    fabricated content. ``is_configured`` is False when no Gemini key is set.
    """
    name: str = ""
    uses: str = ""                          # دواعي الاستعمال
    dosage: str = ""                        # الجرعة الاعتيادية
    sideEffects: List[str] = []             # الآثار الجانبية
    contraindications: List[str] = []       # موانع الاستعمال
    interactions: List[str] = []            # تفاعلات دوائية مهمة
    storage: str = ""                       # طريقة التخزين
    warnings: List[str] = []                # تحذيرات
    recognized: bool = False

    provider: str = "gemini"
    model: str = ""
    is_configured: bool = True
    disclaimer_ar: str = ""
