"""
User Schemas
Pydantic models for user-related request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime, date
from typing import Optional


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
