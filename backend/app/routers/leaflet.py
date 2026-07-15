"""
Leaflet Router
Handles medication leaflet / prescription image upload and returns an
AI-generated Arabic summary produced by a vision-capable LLM.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.leaflet import LeafletSummaryResponse
from app.services.auth_service import get_current_user
from app.services import leaflet_service
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/leaflet", tags=["Leaflet"])


@router.post("/summarize", response_model=LeafletSummaryResponse)
async def summarize_leaflet(
    image: UploadFile = File(..., description="Medication leaflet / prescription photo"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a photo of a medication leaflet (the paper inside the box) or a
    prescription and receive a plain-language summary in Arabic.

    Process:
    1. Validate image file type and size
    2. Send the image to the configured vision LLM (Gemini or OpenAI)
    3. Return the Arabic summary with a safety disclaimer
    """
    # Validate file type
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type. Allowed: {', '.join(settings.ALLOWED_IMAGE_TYPES)}",
        )

    # Read and validate file size
    contents = await image.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty image file.",
        )

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # ── Vision LLM Summarization ──────────────────────────────────────
    # Pass the user so their own API key / provider (set in app settings) is
    # preferred over the server-wide .env defaults.
    try:
        result = await leaflet_service.summarize_leaflet(contents, image.content_type, user, db)
    except leaflet_service.LeafletServiceError as e:
        print(f"[Leaflet Router] Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate the summary. Please try again.",
        )

    return LeafletSummaryResponse(**result)
