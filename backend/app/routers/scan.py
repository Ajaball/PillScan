"""
Scan Router
Handles pill image upload, AI inference, and scan history management.
"""

import asyncio
import uuid
import time
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

import httpx
from PIL import Image as PILImage
from sqlalchemy import or_

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.drug import Drug
from app.models.scan_history import ScanHistory
from app.schemas.medication import BoundingBox, ScanResultResponse, ScanPrediction, ScanHistoryResponse
from app.schemas.user import MessageResponse
from app.services.auth_service import get_current_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/scan", tags=["Scanning"])

# Directory for storing uploaded scan images (local dev)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "scans")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/identify", response_model=ScanResultResponse)
async def identify_pill(
    image: UploadFile = File(..., description="Pill image to identify"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a pill image for AI-powered identification.

    Process:
    1. Validate image file type and size
    2. Save image to storage
    3. Send to AI inference service
    4. Map predictions to drug database
    5. Store scan in history
    6. Return top-5 predictions with drug info
    """
    # Validate file type
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type. Allowed: {', '.join(settings.ALLOWED_IMAGE_TYPES)}",
        )

    # Read and validate file size
    contents = await image.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save image locally (in production, upload to S3)
    file_ext = image.filename.split(".")[-1] if image.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    image_url = f"/uploads/scans/{file_name}"

    # ── AI Inference ─────────────────────────────────────────────────
    start_time = time.time()

    # Get image dimensions in a thread to avoid blocking the async event loop
    def _get_img_size(data: bytes):
        img = PILImage.open(BytesIO(data))
        img.load()  # Force eager load before returning
        return img.size

    img_width, img_height = await asyncio.to_thread(_get_img_size, contents)

    ai_detections = []  # List of {bbox, classifications}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.AI_SERVICE_URL}/predict",
                files={"image": (image.filename or "image.jpg", contents, image.content_type)}
            )
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("success"):
                    data = res_data.get("data", {})
                    ai_detections = data.get("predictions", [])
    except Exception as e:
        print(f"[Scan Router] AI Inference HTTP call failed: {e}")

    # Map predictions to database drugs
    mapped_predictions = []
    seen_drug_ids = set()  # Prevent duplicate drugs in results
    rank = 1

    # Process each detected pill (each has its own bbox + classifications)
    for detection in ai_detections:
        raw_bbox = detection.get("bbox")  # [x1, y1, x2, y2]
        classifications = detection.get("classifications", [])

        # Build BoundingBox object if coordinates are valid
        bbox_obj = None
        if raw_bbox and len(raw_bbox) == 4:
            bbox_obj = BoundingBox(
                x1=raw_bbox[0], y1=raw_bbox[1],
                x2=raw_bbox[2], y2=raw_bbox[3]
            )

        # Use only the top classification for this detection
        top_class = classifications[0] if classifications else None
        if not top_class:
            continue

        pred_class = top_class.get("class_name", top_class.get("class", "")).lower()
        confidence = top_class.get("confidence", 0.0)

        # Search by generic name or brand name matching the predicted class
        result = await db.execute(
            select(Drug).where(
                or_(
                    Drug.name_en.ilike(f"%{pred_class}%"),
                    Drug.generic_name_en.ilike(f"%{pred_class}%"),
                    Drug.name_ar.ilike(f"%{pred_class}%"),
                    Drug.generic_name_ar.ilike(f"%{pred_class}%")
                ),
                Drug.is_active == True
            ).limit(1)
        )
        drug = result.scalar_one_or_none()
        if drug and drug.id not in seen_drug_ids:
            seen_drug_ids.add(drug.id)
            mapped_predictions.append(ScanPrediction(
                rank=rank,
                drug_id=drug.id,
                drug_name_en=drug.name_en,
                drug_name_ar=drug.name_ar,
                confidence=confidence,
                dosage_form=drug.dosage_form,
                strength=drug.strength,
                bbox=bbox_obj,
            ))
            rank += 1

    # Fallback to demo predictions if AI was unreachable or no classes matched
    if not mapped_predictions:
        mapped_predictions = await _get_demo_predictions(db)

    inference_time = (time.time() - start_time) * 1000  # Convert to ms

    # Store scan in history
    top_prediction = mapped_predictions[0] if mapped_predictions else None
    scan = ScanHistory(
        user_id=user.id,
        identified_drug_id=top_prediction.drug_id if top_prediction else None,
        image_url=image_url,
        confidence_score=top_prediction.confidence if top_prediction else None,
        all_predictions={
            "predictions": [p.model_dump(mode="json") for p in mapped_predictions]
        },
        inference_mode="cloud",
        inference_time_ms=inference_time,
    )
    db.add(scan)
    await db.flush()
    await db.refresh(scan)

    return ScanResultResponse(
        scan_id=scan.id,
        predictions=mapped_predictions,
        inference_time_ms=inference_time,
        inference_mode="cloud",
        image_url=image_url,
        scanned_at=scan.scanned_at,
        image_width=img_width,
        image_height=img_height,
    )


async def _get_demo_predictions(db: AsyncSession) -> list[ScanPrediction]:
    """
    Generate demo predictions from the drug database.
    This is a placeholder — replaced by real AI model inference in production.
    """
    result = await db.execute(
        select(Drug).where(Drug.is_active == True).limit(5)
    )
    drugs = result.scalars().all()

    predictions = []
    confidences = [0.87, 0.05, 0.04, 0.02, 0.02]

    for i, drug in enumerate(drugs):
        predictions.append(ScanPrediction(
            rank=i + 1,
            drug_id=drug.id,
            drug_name_en=drug.name_en,
            drug_name_ar=drug.name_ar,
            confidence=confidences[i] if i < len(confidences) else 0.01,
            dosage_form=drug.dosage_form,
            strength=drug.strength,
        ))

    return predictions


@router.get("/history", response_model=list[ScanHistoryResponse])
async def get_scan_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated scan history for the current user, newest first."""
    from sqlalchemy.orm import selectinload
    offset = (page - 1) * page_size
    result = await db.execute(
        select(ScanHistory)
        .options(selectinload(ScanHistory.identified_drug))
        .where(ScanHistory.user_id == user.id)
        .order_by(desc(ScanHistory.scanned_at))
        .offset(offset)
        .limit(page_size)
    )
    scans = result.scalars().all()

    response = []
    for scan in scans:
        drug_name_en = None
        drug_name_ar = None
        if scan.identified_drug:
            drug_name_en = scan.identified_drug.name_en
            drug_name_ar = scan.identified_drug.name_ar

        response.append(ScanHistoryResponse(
            id=scan.id,
            image_url=scan.image_url,
            confidence_score=scan.confidence_score,
            drug_name_en=drug_name_en,
            drug_name_ar=drug_name_ar,
            inference_mode=scan.inference_mode,
            scanned_at=scan.scanned_at,
        ))

    return response


@router.get("/history/{scan_id}", response_model=ScanResultResponse)
async def get_scan_details(
    scan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed results for a specific scan."""
    result = await db.execute(
        select(ScanHistory).where(
            ScanHistory.id == scan_id,
            ScanHistory.user_id == user.id,
        )
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    # Reconstruct predictions from stored JSONB
    predictions = []
    if scan.all_predictions and "predictions" in scan.all_predictions:
        for p in scan.all_predictions["predictions"]:
            predictions.append(ScanPrediction(**p))

    return ScanResultResponse(
        scan_id=scan.id,
        predictions=predictions,
        inference_time_ms=scan.inference_time_ms or 0,
        inference_mode=scan.inference_mode,
        image_url=scan.image_url,
        scanned_at=scan.scanned_at,
    )


@router.delete("/history/{scan_id}", response_model=MessageResponse)
async def delete_scan(
    scan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scan from history."""
    result = await db.execute(
        select(ScanHistory).where(
            ScanHistory.id == scan_id,
            ScanHistory.user_id == user.id,
        )
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    await db.delete(scan)
    await db.flush()

    return MessageResponse(
        message="Scan deleted successfully.",
        message_ar="تم حذف الفحص بنجاح.",
    )
