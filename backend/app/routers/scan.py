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
from app.services import pill_id_service
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

    mapped_predictions: list[ScanPrediction] = []
    inference_source = "unidentified"

    # ── Stage 1: Local CV model (YOLOv8 + EfficientNet) ──────────────
    if settings.SCAN_AI_MODEL_ENABLED:
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

        cv_predictions = await _map_cv_detections(db, ai_detections)

        # Only trust the CV model when its best match clears the threshold.
        if cv_predictions and cv_predictions[0].confidence >= settings.AI_CONFIDENCE_THRESHOLD:
            mapped_predictions = cv_predictions
            inference_source = "ai_model"

    # ── Stage 2: Vision LLM fallback (Gemini / OpenAI) ───────────────
    if not mapped_predictions and settings.SCAN_LLM_FALLBACK_ENABLED:
        try:
            llm_result = await pill_id_service.identify_pill(contents, image.content_type)
        except pill_id_service.PillIdError as e:
            print(f"[Scan Router] LLM identification failed: {e}")
            llm_result = None

        if llm_result and llm_result.get("candidates"):
            llm_predictions = await _map_llm_candidates(db, llm_result["candidates"])
            if llm_predictions:
                mapped_predictions = llm_predictions
                inference_source = "llm"

    # If neither path identified the pill, return an honest empty result
    # (no fabricated "demo" match).

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
        inference_mode=inference_source,
        inference_time_ms=inference_time,
    )
    db.add(scan)
    await db.flush()
    await db.refresh(scan)

    return ScanResultResponse(
        scan_id=scan.id,
        predictions=mapped_predictions,
        inference_time_ms=inference_time,
        inference_mode=inference_source,
        image_url=image_url,
        scanned_at=scan.scanned_at,
        image_width=img_width,
        image_height=img_height,
    )


async def _find_drug(db: AsyncSession, term: str) -> Optional[Drug]:
    """Look up an active drug by a brand/generic term (EN or AR), if any."""
    term = (term or "").strip()
    if not term:
        return None
    result = await db.execute(
        select(Drug).where(
            or_(
                Drug.name_en.ilike(f"%{term}%"),
                Drug.generic_name_en.ilike(f"%{term}%"),
                Drug.name_ar.ilike(f"%{term}%"),
                Drug.generic_name_ar.ilike(f"%{term}%"),
            ),
            Drug.is_active == True,
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def _map_cv_detections(db: AsyncSession, ai_detections: list) -> list[ScanPrediction]:
    """Map CV-model detections (bbox + classifications) to database drugs."""
    mapped: list[ScanPrediction] = []
    seen_drug_ids = set()  # Prevent duplicate drugs in results
    rank = 1

    for detection in ai_detections:
        raw_bbox = detection.get("bbox")  # [x1, y1, x2, y2]
        classifications = detection.get("classifications", [])

        bbox_obj = None
        if raw_bbox and len(raw_bbox) == 4:
            bbox_obj = BoundingBox(
                x1=raw_bbox[0], y1=raw_bbox[1],
                x2=raw_bbox[2], y2=raw_bbox[3],
            )

        top_class = classifications[0] if classifications else None
        if not top_class:
            continue

        pred_class = top_class.get("class_name", top_class.get("class", "")).lower()
        confidence = top_class.get("confidence", 0.0)

        drug = await _find_drug(db, pred_class)
        if drug and drug.id not in seen_drug_ids:
            seen_drug_ids.add(drug.id)
            mapped.append(ScanPrediction(
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

    return mapped


async def _map_llm_candidates(db: AsyncSession, candidates: list) -> list[ScanPrediction]:
    """
    Map vision-LLM candidates to database drugs. Candidates that match a
    seeded drug are enriched with its details; unmatched candidates are still
    surfaced using the model's own identification (drug_id = None).
    """
    mapped: list[ScanPrediction] = []
    seen_drug_ids = set()
    rank = 1

    for cand in candidates:
        name_en = cand.get("name_en", "")
        name_ar = cand.get("name_ar", "")
        generic = cand.get("generic_en", "")
        confidence = float(cand.get("confidence", 0.0) or 0.0)

        # Try to match a seeded drug by brand, then generic, then Arabic name.
        drug = None
        for term in (name_en, generic, name_ar):
            drug = await _find_drug(db, term)
            if drug:
                break

        if drug:
            if drug.id in seen_drug_ids:
                continue
            seen_drug_ids.add(drug.id)
            mapped.append(ScanPrediction(
                rank=rank,
                drug_id=drug.id,
                drug_name_en=drug.name_en,
                drug_name_ar=drug.name_ar,
                confidence=confidence,
                dosage_form=drug.dosage_form,
                strength=drug.strength,
                bbox=None,
            ))
        else:
            # Not in our database — surface the LLM's own identification.
            mapped.append(ScanPrediction(
                rank=rank,
                drug_id=None,
                drug_name_en=name_en or name_ar,
                drug_name_ar=name_ar or name_en,
                confidence=confidence,
                dosage_form=cand.get("dosage_form") or None,
                strength=cand.get("strength") or None,
                bbox=None,
            ))
        rank += 1

    return mapped


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


@router.get("/llm-diagnostics")
async def llm_diagnostics(user: User = Depends(get_current_user)):
    """
    Diagnose the vision-LLM identification path.

    Reports what the *running* backend actually sees (provider, model, whether
    an API key is configured) and performs a tiny live text-only call to the
    provider so a misconfigured key / disabled API / restricted key surfaces as
    a concrete error instead of a silent "not identified". The API key itself is
    never returned.
    """
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    model = settings.OPENAI_MODEL if provider == "openai" else settings.GEMINI_MODEL
    configured = pill_id_service.is_configured()

    result = {
        "scan_ai_model_enabled": settings.SCAN_AI_MODEL_ENABLED,
        "scan_llm_fallback_enabled": settings.SCAN_LLM_FALLBACK_ENABLED,
        "provider": provider,
        "model": model,
        "api_key_configured": configured,
        "live_call_ok": None,
        "live_call_detail": None,
    }

    if not configured:
        result["live_call_detail"] = (
            "No API key detected for the selected provider. Set "
            + ("OPENAI_API_KEY" if provider == "openai" else "GEMINI_API_KEY")
            + " in the backend environment and redeploy."
        )
        return result

    # Minimal live ping (text only, no image) to validate the key/model.
    try:
        if provider == "openai":
            url = f"{settings.OPENAI_API_BASE}/chat/completions"
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            payload = {
                "model": settings.OPENAI_MODEL,
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Reply with the word OK."}],
            }
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                resp = await client.post(url, headers=headers, json=payload)
        else:
            url = (
                f"{settings.GEMINI_API_BASE}/models/{settings.GEMINI_MODEL}:generateContent"
                f"?key={settings.GEMINI_API_KEY}"
            )
            payload = {"contents": [{"parts": [{"text": "Reply with the word OK."}]}]}
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                resp = await client.post(url, json=payload)

        if resp.status_code == 200:
            result["live_call_ok"] = True
            result["live_call_detail"] = "Provider reachable and key accepted."
        else:
            result["live_call_ok"] = False
            # Provider error bodies do not contain the key; safe to surface.
            result["live_call_detail"] = f"HTTP {resp.status_code}: {resp.text[:300]}"
    except Exception as e:  # noqa: BLE001 - report any failure to the caller
        result["live_call_ok"] = False
        result["live_call_detail"] = f"{type(e).__name__}: {str(e)[:300]}"

    return result
