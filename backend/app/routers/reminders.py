"""
Reminder Router
Handles medication reminder CRUD and snooze functionality.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.reminder import Reminder
from app.models.medication import Medication
from app.schemas.medication import (
    ReminderCreateRequest,
    ReminderUpdateRequest,
    ReminderResponse,
)
from app.schemas.user import MessageResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.get("/", response_model=list[ReminderResponse])
async def list_reminders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reminders for the current user."""
    result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == user.id)
        .order_by(Reminder.reminder_time)
    )
    reminders = result.scalars().all()

    response = []
    for rem in reminders:
        med_name = None
        if rem.medication:
            med_name = rem.medication.custom_name
            if not med_name and rem.medication.drug:
                med_name = rem.medication.drug.name_en

        response.append(ReminderResponse(
            id=rem.id,
            user_id=rem.user_id,
            medication_id=rem.medication_id,
            reminder_time=rem.reminder_time,
            days_of_week=rem.days_of_week,
            is_active=rem.is_active,
            notification_title=rem.notification_title,
            notification_body=rem.notification_body,
            snooze_minutes=rem.snooze_minutes,
            created_at=rem.created_at,
            medication_name=med_name,
        ))

    return response


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    request: ReminderCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new medication reminder."""
    # Verify medication belongs to user
    result = await db.execute(
        select(Medication).where(
            Medication.id == request.medication_id,
            Medication.user_id == user.id,
        )
    )
    medication = result.scalar_one_or_none()

    if not medication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found or doesn't belong to you",
        )

    reminder = Reminder(
        user_id=user.id,
        medication_id=request.medication_id,
        reminder_time=request.reminder_time,
        days_of_week=request.days_of_week,
        notification_title=request.notification_title or f"Time to take your medication",
        notification_body=request.notification_body,
        snooze_minutes=request.snooze_minutes,
    )
    db.add(reminder)
    await db.flush()
    await db.refresh(reminder)

    med_name = medication.custom_name
    if not med_name and medication.drug:
        med_name = medication.drug.name_en

    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medication_id=reminder.medication_id,
        reminder_time=reminder.reminder_time,
        days_of_week=reminder.days_of_week,
        is_active=reminder.is_active,
        notification_title=reminder.notification_title,
        notification_body=reminder.notification_body,
        snooze_minutes=reminder.snooze_minutes,
        created_at=reminder.created_at,
        medication_name=med_name,
    )


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    request: ReminderUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing reminder."""
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user.id,
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)

    await db.flush()
    await db.refresh(reminder)

    med_name = None
    if reminder.medication:
        med_name = reminder.medication.custom_name
        if not med_name and reminder.medication.drug:
            med_name = reminder.medication.drug.name_en

    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        medication_id=reminder.medication_id,
        reminder_time=reminder.reminder_time,
        days_of_week=reminder.days_of_week,
        is_active=reminder.is_active,
        notification_title=reminder.notification_title,
        notification_body=reminder.notification_body,
        snooze_minutes=reminder.snooze_minutes,
        created_at=reminder.created_at,
        medication_name=med_name,
    )


@router.delete("/{reminder_id}", response_model=MessageResponse)
async def delete_reminder(
    reminder_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a reminder."""
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user.id,
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    await db.delete(reminder)
    await db.flush()

    return MessageResponse(
        message="Reminder deleted successfully.",
        message_ar="تم حذف التنبيه بنجاح.",
    )


@router.post("/{reminder_id}/snooze", response_model=MessageResponse)
async def snooze_reminder(
    reminder_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Snooze a reminder for the configured snooze duration.
    In a real implementation, this would reschedule the push notification.
    """
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user.id,
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    # In production: reschedule FCM notification for snooze_minutes later
    return MessageResponse(
        message=f"Reminder snoozed for {reminder.snooze_minutes} minutes.",
        message_ar=f"تم تأجيل التنبيه لمدة {reminder.snooze_minutes} دقائق.",
    )
