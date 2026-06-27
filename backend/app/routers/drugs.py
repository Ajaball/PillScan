"""
Drug Information Router
Handles drug search, listing, and detailed information retrieval.
Admin endpoints for drug database management.
"""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.drug import Drug, DrugImage, DrugSideEffect, DrugContraindication
from app.models.user import User
from app.schemas.drug import (
    DrugListResponse,
    DrugDetailResponse,
    DrugCreateRequest,
    DrugUpdateRequest,
    DrugImageResponse,
)
from app.schemas.user import MessageResponse
from app.services.auth_service import get_current_user, get_current_admin

router = APIRouter(prefix="/drugs", tags=["Drugs"])


@router.get("/search", response_model=list[DrugListResponse])
async def search_drugs(
    q: Optional[str] = Query(None, min_length=1, description="Search query (name)"),
    shape: Optional[str] = Query(None, description="Pill shape filter"),
    color: Optional[str] = Query(None, description="Pill color filter"),
    category: Optional[str] = Query(None, description="Drug category filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Search drugs by name, shape, color, or category.
    Free-text search matches against both English and Arabic names.
    """
    query = select(Drug).where(Drug.is_active == True).options(selectinload(Drug.images))

    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Drug.name_en.ilike(search_term),
                Drug.name_ar.ilike(search_term),
                Drug.generic_name_en.ilike(search_term),
                Drug.generic_name_ar.ilike(search_term),
            )
        )

    if shape:
        query = query.where(Drug.shape == shape.lower())
    if color:
        query = query.where(Drug.color == color.lower())
    if category:
        query = query.where(Drug.category == category)

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Drug.name_en)

    result = await db.execute(query)
    drugs = result.scalars().all()

    # Map to response with primary image
    response = []
    for drug in drugs:
        primary_image = None
        if drug.images:
            primary = next((img for img in drug.images if img.is_primary), None)
            primary_image = primary.image_url if primary else drug.images[0].image_url

        response.append(DrugListResponse(
            id=drug.id,
            name_en=drug.name_en,
            name_ar=drug.name_ar,
            generic_name_en=drug.generic_name_en,
            generic_name_ar=drug.generic_name_ar,
            dosage_form=drug.dosage_form,
            strength=drug.strength,
            shape=drug.shape,
            color=drug.color,
            category=drug.category,
            primary_image_url=primary_image,
        ))

    return response


@router.get("/{drug_id}", response_model=DrugDetailResponse)
async def get_drug_details(
    drug_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get full drug details including images, side effects, and contraindications."""
    result = await db.execute(
        select(Drug)
        .where(Drug.id == drug_id, Drug.is_active == True)
        .options(
            selectinload(Drug.images),
            selectinload(Drug.side_effects),
            selectinload(Drug.contraindications),
        )
    )
    drug = result.scalar_one_or_none()

    if not drug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug not found",
        )

    return drug


@router.get("/{drug_id}/images", response_model=list[DrugImageResponse])
async def get_drug_images(
    drug_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all images for a specific drug."""
    result = await db.execute(
        select(DrugImage).where(DrugImage.drug_id == drug_id)
    )
    images = result.scalars().all()
    return images


# ── Admin Endpoints ──────────────────────────────────────────────────────

@router.post("/", response_model=DrugDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_drug(
    request: DrugCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """[Admin] Create a new drug entry in the database."""
    drug = Drug(**request.model_dump())
    db.add(drug)
    await db.flush()
    
    # Reload with options to prevent lazy load serialization errors
    result = await db.execute(
        select(Drug)
        .where(Drug.id == drug.id)
        .options(
            selectinload(Drug.images),
            selectinload(Drug.side_effects),
            selectinload(Drug.contraindications),
        )
    )
    return result.scalar_one()


@router.put("/{drug_id}", response_model=DrugDetailResponse)
async def update_drug(
    drug_id: UUID,
    request: DrugUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """[Admin] Update an existing drug entry."""
    result = await db.execute(select(Drug).where(Drug.id == drug_id))
    drug = result.scalar_one_or_none()

    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(drug, field, value)

    await db.flush()
    
    # Reload with options to prevent lazy load serialization errors
    updated_result = await db.execute(
        select(Drug)
        .where(Drug.id == drug_id)
        .options(
            selectinload(Drug.images),
            selectinload(Drug.side_effects),
            selectinload(Drug.contraindications),
        )
    )
    return updated_result.scalar_one()


@router.delete("/{drug_id}", response_model=MessageResponse)
async def delete_drug(
    drug_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """[Admin] Soft-delete a drug (set is_active=False)."""
    result = await db.execute(select(Drug).where(Drug.id == drug_id))
    drug = result.scalar_one_or_none()

    if not drug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found")

    drug.is_active = False
    await db.flush()

    return MessageResponse(
        message=f"Drug '{drug.name_en}' has been deactivated.",
        message_ar=f"تم تعطيل الدواء '{drug.name_ar}'.",
    )
