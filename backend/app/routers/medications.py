"""
Medication Management Router
Handles CRUD operations for user medications.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.medication import Medication
from app.models.drug import Drug
from app.schemas.medication import (
    MedicationCreateRequest,
    MedicationUpdateRequest,
    MedicationResponse,
)
from app.schemas.user import MessageResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/medications", tags=["Medications"])


@router.get("/", response_model=list[MedicationResponse])
async def list_medications(
    active_only: bool = Query(True, description="Show only active medications"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all medications for the current user."""
    # Eager-load the drug relationship: with an async session a lazy load here
    # would raise MissingGreenlet (→ 500).
    query = (
        select(Medication)
        .options(selectinload(Medication.drug))
        .where(Medication.user_id == user.id)
    )
    if active_only:
        query = query.where(Medication.is_active == True)
    query = query.order_by(Medication.created_at.desc())

    result = await db.execute(query)
    medications = result.scalars().all()

    response = []
    for med in medications:
        drug_name_en = None
        drug_name_ar = None
        if med.drug:
            drug_name_en = med.drug.name_en
            drug_name_ar = med.drug.name_ar

        response.append(MedicationResponse(
            id=med.id,
            user_id=med.user_id,
            drug_id=med.drug_id,
            custom_name=med.custom_name,
            dosage=med.dosage,
            frequency=med.frequency,
            start_date=med.start_date,
            end_date=med.end_date,
            notes=med.notes,
            is_active=med.is_active,
            created_at=med.created_at,
            drug_name_en=drug_name_en,
            drug_name_ar=drug_name_ar,
        ))

    return response


@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    request: MedicationCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new medication to the user's list.
    Can be linked to a drug from the database or have a custom name.
    """
    # Validate drug_id if provided
    drug = None
    if request.drug_id:
        result = await db.execute(select(Drug).where(Drug.id == request.drug_id))
        drug = result.scalar_one_or_none()
        if not drug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Drug not found in database",
            )

    if not request.drug_id and not request.custom_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either drug_id or custom_name must be provided",
        )

    medication = Medication(
        user_id=user.id,
        drug_id=request.drug_id,
        custom_name=request.custom_name,
        dosage=request.dosage,
        frequency=request.frequency,
        start_date=request.start_date,
        end_date=request.end_date,
        notes=request.notes,
    )
    db.add(medication)
    await db.flush()
    await db.refresh(medication)

    return MedicationResponse(
        id=medication.id,
        user_id=medication.user_id,
        drug_id=medication.drug_id,
        custom_name=medication.custom_name,
        dosage=medication.dosage,
        frequency=medication.frequency,
        start_date=medication.start_date,
        end_date=medication.end_date,
        notes=medication.notes,
        is_active=medication.is_active,
        created_at=medication.created_at,
        drug_name_en=drug.name_en if drug else None,
        drug_name_ar=drug.name_ar if drug else None,
    )


@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: UUID,
    request: MedicationUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing medication."""
    result = await db.execute(
        select(Medication).where(
            Medication.id == medication_id,
            Medication.user_id == user.id,
        )
    )
    medication = result.scalar_one_or_none()

    if not medication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(medication, field, value)

    await db.flush()

    # Re-load with the drug eager-loaded (async lazy access would 500 otherwise).
    reloaded = await db.execute(
        select(Medication)
        .options(selectinload(Medication.drug))
        .where(Medication.id == medication_id)
    )
    medication = reloaded.scalar_one()

    drug_name_en = medication.drug.name_en if medication.drug else None
    drug_name_ar = medication.drug.name_ar if medication.drug else None

    return MedicationResponse(
        id=medication.id,
        user_id=medication.user_id,
        drug_id=medication.drug_id,
        custom_name=medication.custom_name,
        dosage=medication.dosage,
        frequency=medication.frequency,
        start_date=medication.start_date,
        end_date=medication.end_date,
        notes=medication.notes,
        is_active=medication.is_active,
        created_at=medication.created_at,
        drug_name_en=drug_name_en,
        drug_name_ar=drug_name_ar,
    )


@router.delete("/{medication_id}", response_model=MessageResponse)
async def delete_medication(
    medication_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a medication (and its associated reminders via cascade)."""
    result = await db.execute(
        select(Medication).where(
            Medication.id == medication_id,
            Medication.user_id == user.id,
        )
    )
    medication = result.scalar_one_or_none()

    if not medication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    await db.delete(medication)
    await db.flush()

    return MessageResponse(
        message="Medication removed successfully.",
        message_ar="تم حذف الدواء بنجاح.",
    )
