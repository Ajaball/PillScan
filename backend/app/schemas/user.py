"""
User Schemas
Pydantic models for user-related request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional


# ── Request Schemas ──────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{8,15}$")
    language: str = Field(default="ar", pattern=r"^(ar|en)$")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{8,15}$")
    language: Optional[str] = Field(None, pattern=r"^(ar|en)$")
    date_of_birth: Optional[date] = None
    medical_conditions: Optional[dict] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangeLanguageRequest(BaseModel):
    language: str = Field(..., pattern=r"^(ar|en)$")


class AISettingsUpdateRequest(BaseModel):
    """
    Update the user's Gemini API keys (up to five, tried in order).

    All fields are optional so the client can update just one slot:
    - Send a key string to set/replace it.
    - Send an empty string ("") to clear a stored key.
    - Omit a field to leave it unchanged.
    """
    gemini_api_key: Optional[str] = Field(None, max_length=512)
    gemini_api_key_2: Optional[str] = Field(None, max_length=512)
    gemini_api_key_3: Optional[str] = Field(None, max_length=512)
    gemini_api_key_4: Optional[str] = Field(None, max_length=512)
    gemini_api_key_5: Optional[str] = Field(None, max_length=512)


# ── Response Schemas ─────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: UUID
    email: str
    phone: Optional[str] = None
    full_name: str
    language: str
    date_of_birth: Optional[date] = None
    medical_conditions: Optional[dict] = None
    profile_image_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class MessageResponse(BaseModel):
    message: str
    message_ar: Optional[str] = None


class GeminiKeyStatus(BaseModel):
    """Status of one Gemini key slot — never exposes the raw key."""
    slot: int                               # 1..5
    configured: bool                        # True if a key is stored in this slot
    hint: Optional[str] = None              # e.g. "••••••••abcd"


class AISettingsResponse(BaseModel):
    """
    The user's Gemini keys — never exposes the raw API keys, only whether each
    slot is configured plus a masked hint. Keys are tried in slot order with
    automatic failover.
    """
    provider: str = "gemini"
    keys: List[GeminiKeyStatus]
    configured_count: int
