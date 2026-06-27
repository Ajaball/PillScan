"""
Drug Schemas
Pydantic models for drug-related request/response validation.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


# ── Response Schemas ─────────────────────────────────────────────────────

class DrugSideEffectResponse(BaseModel):
    id: UUID
    effect_en: str
    effect_ar: str
    severity: str

    model_config = {"from_attributes": True}


class DrugContraindicationResponse(BaseModel):
    id: UUID
    contraindication_en: str
    contraindication_ar: str

    model_config = {"from_attributes": True}


class DrugImageResponse(BaseModel):
    id: UUID
    image_url: str
    image_type: str
    is_primary: bool

    model_config = {"from_attributes": True}


class DrugListResponse(BaseModel):
    """Compact drug info for list views and search results."""
    id: UUID
    name_en: str
    name_ar: str
    generic_name_en: Optional[str] = None
    generic_name_ar: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    shape: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    primary_image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class DrugDetailResponse(BaseModel):
    """Full drug detail view with all related data."""
    id: UUID
    name_en: str
    name_ar: str
    generic_name_en: Optional[str] = None
    generic_name_ar: Optional[str] = None
    manufacturer: Optional[str] = None
    ndc_code: Optional[str] = None
    sfda_reg_number: Optional[str] = None
    shape: Optional[str] = None
    color: Optional[str] = None
    imprint: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    usage_instructions_en: Optional[str] = None
    usage_instructions_ar: Optional[str] = None
    storage_instructions: Optional[str] = None
    category: Optional[str] = None
    requires_prescription: bool
    images: list[DrugImageResponse] = []
    side_effects: list[DrugSideEffectResponse] = []
    contraindications: list[DrugContraindicationResponse] = []

    model_config = {"from_attributes": True}


# ── Request Schemas (Admin) ──────────────────────────────────────────────

class DrugCreateRequest(BaseModel):
    name_en: str = Field(..., min_length=1, max_length=255)
    name_ar: str = Field(..., min_length=1, max_length=255)
    generic_name_en: Optional[str] = None
    generic_name_ar: Optional[str] = None
    manufacturer: Optional[str] = None
    ndc_code: Optional[str] = None
    sfda_reg_number: Optional[str] = None
    shape: Optional[str] = None
    color: Optional[str] = None
    imprint: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    usage_instructions_en: Optional[str] = None
    usage_instructions_ar: Optional[str] = None
    storage_instructions: Optional[str] = None
    category: Optional[str] = None
    requires_prescription: bool = False
    model_class_id: Optional[int] = None


class DrugUpdateRequest(BaseModel):
    name_en: Optional[str] = Field(None, min_length=1, max_length=255)
    name_ar: Optional[str] = Field(None, min_length=1, max_length=255)
    generic_name_en: Optional[str] = None
    generic_name_ar: Optional[str] = None
    manufacturer: Optional[str] = None
    shape: Optional[str] = None
    color: Optional[str] = None
    imprint: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    usage_instructions_en: Optional[str] = None
    usage_instructions_ar: Optional[str] = None
    storage_instructions: Optional[str] = None
    category: Optional[str] = None
    requires_prescription: Optional[bool] = None


# ── Search Schema ────────────────────────────────────────────────────────

class DrugSearchParams(BaseModel):
    q: Optional[str] = None  # Free-text search
    shape: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
