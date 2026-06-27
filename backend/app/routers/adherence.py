"""
Adherence Tracking Router
Handles medication adherence logging, statistics, and calendar views.
"""

from uuid import UUID
from datetime import datetime, date, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.user import User
from app.models.medication import Medication
from app.models.adherence import AdherenceLog
from app.schemas.medication import (
    AdherenceLogRequest,
    AdherenceLogResponse,
    AdherenceStatsResponse,
    AdherenceCalendarResponse,
    AdherenceCalendarDay,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/adherence", tags=["Adherence"])


@router.post("/log", response_model=AdherenceLogResponse, status_code=status.HTTP_201_CREATED)
async def log_adherence(
    request: AdherenceLogRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Log a medication event — taken, skipped, or missed.
    Called when user responds to a reminder.
    """
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
            detail="Medication not found",
        )

    log = AdherenceLog(
        user_id=user.id,
        medication_id=request.medication_id,
        status=request.status,
        scheduled_time=request.scheduled_time,
        actual_time=request.actual_time or (datetime.now(timezone.utc) if request.status == "taken" else None),
        notes=request.notes,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)

    return log


@router.get("/stats", response_model=AdherenceStatsResponse)
async def get_adherence_stats(
    period: str = Query("week", pattern=r"^(week|month|year)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get adherence statistics for a given period.
    Returns total, taken, skipped, missed counts and adherence rate.
    """
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)

    result = await db.execute(
        select(AdherenceLog).where(
            AdherenceLog.user_id == user.id,
            AdherenceLog.scheduled_time >= start_date,
        )
    )
    logs = result.scalars().all()

    total = len(logs)
    taken = sum(1 for log in logs if log.status == "taken")
    skipped = sum(1 for log in logs if log.status == "skipped")
    missed = sum(1 for log in logs if log.status == "missed")

    adherence_rate = (taken / total * 100) if total > 0 else 0.0

    # Calculate streak (consecutive days with all medications taken)
    streak = await _calculate_streak(user.id, db)

    return AdherenceStatsResponse(
        period=period,
        total_scheduled=total,
        taken=taken,
        skipped=skipped,
        missed=missed,
        adherence_rate=round(adherence_rate, 1),
        streak_days=streak,
    )


@router.get("/calendar", response_model=AdherenceCalendarResponse)
async def get_adherence_calendar(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a calendar view of adherence data for a specific month.
    Returns per-day breakdown of taken/skipped/missed.
    """
    year, month_num = map(int, month.split("-"))
    start = datetime(year, month_num, 1, tzinfo=timezone.utc)
    if month_num == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, month_num + 1, 1, tzinfo=timezone.utc)

    result = await db.execute(
        select(AdherenceLog).where(
            AdherenceLog.user_id == user.id,
            AdherenceLog.scheduled_time >= start,
            AdherenceLog.scheduled_time < end,
        )
    )
    logs = result.scalars().all()

    # Group by date
    days_map: dict[date, dict] = {}
    for log in logs:
        day = log.scheduled_time.date()
        if day not in days_map:
            days_map[day] = {"total": 0, "taken": 0, "skipped": 0, "missed": 0}
        days_map[day]["total"] += 1
        days_map[day][log.status] += 1

    days = []
    for day, counts in sorted(days_map.items()):
        days.append(AdherenceCalendarDay(
            date=day,
            total=counts["total"],
            taken=counts["taken"],
            skipped=counts["skipped"],
            missed=counts["missed"],
        ))

    return AdherenceCalendarResponse(month=month, days=days)


@router.get("/streak")
async def get_adherence_streak(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the user's current consecutive days adherence streak.
    """
    streak = await _calculate_streak(user.id, db)
    return {"streak_days": streak}


async def _calculate_streak(user_id: UUID, db: AsyncSession) -> int:
    """
    Calculate the current streak of consecutive days where the user
    took all scheduled medications.
    """
    today = datetime.now(timezone.utc).date()
    streak = 0

    for days_back in range(365):  # Max 1 year lookback
        check_date = today - timedelta(days=days_back)
        start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        result = await db.execute(
            select(AdherenceLog).where(
                AdherenceLog.user_id == user_id,
                AdherenceLog.scheduled_time >= start,
                AdherenceLog.scheduled_time < end,
            )
        )
        day_logs = result.scalars().all()

        if not day_logs:
            break  # No scheduled medications this day — streak ends

        all_taken = all(log.status == "taken" for log in day_logs)
        if all_taken:
            streak += 1
        else:
            break

    return streak
