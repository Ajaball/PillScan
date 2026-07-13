"""
User Profile Router
Handles user profile retrieval and updates.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserUpdateRequest,
    ChangeLanguageRequest,
    MessageResponse,
    AISettingsUpdateRequest,
    AISettingsResponse,
    GeminiKeyStatus,
)
from app.services.auth_service import get_current_user
from app.config import get_settings
from app.utils.crypto import encrypt_secret, decrypt_secret, mask_secret

router = APIRouter(prefix="/users", tags=["Users"])
settings = get_settings()


@router.get("/me", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile information."""
    update_data = request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


@router.put("/me/language", response_model=MessageResponse)
async def change_language(
    request: ChangeLanguageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the user's preferred language (ar/en)."""
    user.language = request.language
    await db.flush()

    if request.language == "ar":
        return MessageResponse(
            message="Language changed to Arabic.",
            message_ar="تم تغيير اللغة إلى العربية.",
        )
    return MessageResponse(
        message="Language changed to English.",
        message_ar="تم تغيير اللغة إلى الإنجليزية.",
    )


# ── AI / Leaflet Summarizer Settings ─────────────────────────────────────

_KEY_SLOTS = 5


def _slot_attr(slot: int) -> str:
    """Model attribute for a Gemini key slot (1-based)."""
    return "gemini_api_key" if slot == 1 else f"gemini_api_key_{slot}"


def _build_ai_settings_response(user: User) -> AISettingsResponse:
    """Shape the user's Gemini keys for the client (never exposes raw keys)."""
    keys = []
    configured = 0
    for slot in range(1, _KEY_SLOTS + 1):
        raw = decrypt_secret(getattr(user, _slot_attr(slot), None))
        if raw:
            configured += 1
        keys.append(GeminiKeyStatus(slot=slot, configured=bool(raw), hint=mask_secret(raw)))
    return AISettingsResponse(provider="gemini", keys=keys, configured_count=configured)


@router.get("/me/ai-settings", response_model=AISettingsResponse)
async def get_ai_settings(user: User = Depends(get_current_user)):
    """
    Get the current user's AI (leaflet summarizer) settings.
    Returns only whether each provider is configured plus a masked hint —
    the raw API keys are never sent back to the client.
    """
    return _build_ai_settings_response(user)


@router.put("/me/ai-settings", response_model=AISettingsResponse)
async def update_ai_settings(
    request: AISettingsUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current user's AI settings.

    - Provide a key to set/replace it; keys are encrypted before storage.
    - Provide an empty string ("") to clear a stored key.
    - Omit a field to leave it unchanged.
    """
    update_data = request.model_dump(exclude_unset=True)

    for slot in range(1, _KEY_SLOTS + 1):
        attr = _slot_attr(slot)
        if attr in update_data:
            setattr(user, attr, encrypt_secret((update_data[attr] or "").strip()))

    await db.flush()
    await db.refresh(user)
    return _build_ai_settings_response(user)
