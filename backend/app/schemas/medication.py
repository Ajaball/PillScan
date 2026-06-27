"""
Medication & Reminder Schemas
Pydantic models for medication management and reminder scheduling.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date, time
from typing import Optional


# ── Medication Schemas ───────────────────────────────────────────────────

class MedicationCreateRequest(BaseModel):
    drug_id: Optional[UUID] = None
    custom_name: Optional[str] = Field(None, max_length=255)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: str = Field(default="once_daily", pattern=r"^(once_daily|twice_daily|three_times_daily|weekly|custom)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class MedicationUpdateRequest(BaseModel):
    custom_name: Optional[str] = Field(None, max_length=255)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, pattern=r"^(once_daily|twice_daily|three_times_daily|weekly|custom)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MedicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    drug_id: Optional[UUID] = None
    custom_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    # Nested drug info (compact)
    drug_name_en: Optional[str] = None
    drug_name_ar: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Reminder Schemas ─────────────────────────────────────────────────────

class ReminderCreateRequest(BaseModel):
    medication_id: UUID
    reminder_time: time
    days_of_week: Optional[list[int]] = None  # 0=Mon, 6=Sun; null=every day
    notification_title: Optional[str] = Field(None, max_length=255)
    notification_body: Optional[str] = Field(None, max_length=500)
    snooze_minutes: int = Field(default=10, ge=1, le=60)


class ReminderUpdateRequest(BaseModel):
    reminder_time: Optional[time] = None
    days_of_week: Optional[list[int]] = None
    is_active: Optional[bool] = None
    notification_title: Optional[str] = Field(None, max_length=255)
    notification_body: Optional[str] = Field(None, max_length=500)
    snooze_minutes: Optional[int] = Field(None, ge=1, le=60)


class ReminderResponse(BaseModel):
    id: UUID
    user_id: UUID
    medication_id: UUID
    reminder_time: time
    days_of_week: Optional[list] = None
    is_active: bool
    notification_title: Optional[str] = None
    notification_body: Optional[str] = None
    snooze_minutes: int
    created_at: datetime
    # Nested medication info
    medication_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Adherence Schemas ────────────────────────────────────────────────────

class AdherenceLogRequest(BaseModel):
    medication_id: UUID
    status: str = Field(..., pattern=r"^(taken|skipped|missed)$")
    scheduled_time: datetime
    actual_time: Optional[datetime] = None
    notes: Optional[str] = None


class AdherenceLogResponse(BaseModel):
    id: UUID
    medication_id: UUID
    status: str
    scheduled_time: datetime
    actual_time: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdherenceStatsResponse(BaseModel):
    period: str  # 'week' | 'month' | 'year'
    total_scheduled: int
    taken: int
    skipped: int
    missed: int
    adherence_rate: float  # percentage 0-100
    streak_days: int


class AdherenceCalendarDay(BaseModel):
    date: date
    total: int
    taken: int
    skipped: int
    missed: int


class AdherenceCalendarResponse(BaseModel):
    month: str  # 'YYYY-MM'
    days: list[AdherenceCalendarDay]


# ── Scan Schemas ─────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Pixel coordinates of a detected pill: [x1, y1, x2, y2]"""
    x1: float
    y1: float
    x2: float
    y2: float


class ScanPrediction(BaseModel):
    rank: int
    drug_id: Optional[UUID] = None
    drug_name_en: Optional[str] = None
    drug_name_ar: Optional[str] = None
    confidence: float
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    bbox: Optional[BoundingBox] = None  # Bounding box of the detected pill


class ScanResultResponse(BaseModel):
    scan_id: UUID
    predictions: list[ScanPrediction]
    inference_time_ms: float
    inference_mode: str
    image_url: str
    scanned_at: datetime
    image_width: Optional[int] = None   # Original image dimensions for scaling
    image_height: Optional[int] = None

    model_config = {"from_attributes": True}


class ScanHistoryResponse(BaseModel):
    id: UUID
    image_url: str
    confidence_score: Optional[float] = None
    drug_name_en: Optional[str] = None
    drug_name_ar: Optional[str] = None
    inference_mode: str
    scanned_at: datetime

    model_config = {"from_attributes": True}
