"""
User Profile Router
Handles user profile retrieval and updates.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest, ChangeLanguageRequest, MessageResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


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
