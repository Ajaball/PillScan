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

def _build_ai_settings_response(user: User) -> AISettingsResponse:
    """Shape the user's AI settings for the client (never exposes raw keys)."""
    gemini_key = decrypt_secret(user.gemini_api_key)
    openai_key = decrypt_secret(user.openai_api_key)
    provider = (user.llm_provider or settings.LLM_PROVIDER or "gemini").lower()
    return AISettingsResponse(
        llm_provider=provider,
        gemini_configured=bool(gemini_key),
        openai_configured=bool(openai_key),
        gemini_key_hint=mask_secret(gemini_key),
        openai_key_hint=mask_secret(openai_key),
    )


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

    if "gemini_api_key" in update_data:
        user.gemini_api_key = encrypt_secret((update_data["gemini_api_key"] or "").strip())
    if "openai_api_key" in update_data:
        user.openai_api_key = encrypt_secret((update_data["openai_api_key"] or "").strip())
    if "llm_provider" in update_data and update_data["llm_provider"]:
        user.llm_provider = update_data["llm_provider"]

    await db.flush()
    await db.refresh(user)
    return _build_ai_settings_response(user)
