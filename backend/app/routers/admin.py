"""
Admin Router
Admin-only endpoints for the user approval workflow: list users (optionally
filtered by approval status) and change a user's status (approve / reject).

Every endpoint depends on ``get_current_admin`` so access is enforced on the
**server** — a non-admin token is rejected here regardless of what the UI shows.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.scan_history import ScanHistory
from app.models.medication import Medication
from app.models.reminder import Reminder
from app.models.user_query import UserQuery
from app.schemas.user import AdminUserResponse, UpdateUserStatusRequest
from app.services.auth_service import get_current_admin
from app.config import get_settings

router = APIRouter(prefix="/admin", tags=["Admin"])
settings = get_settings()


@router.get("/db-status")
async def db_status(admin: User = Depends(get_current_admin)):
    """
    [Admin] Report whether storage is persistent so the admin can see at a
    glance if data survives redeploys. Never exposes credentials — only the
    engine type and host (host shown for Postgres so it's clear which DB).
    """
    url = settings.DATABASE_URL or ""
    is_sqlite = url.startswith("sqlite")
    host = None
    if not is_sqlite:
        from urllib.parse import urlsplit
        host = urlsplit(url).hostname

    return {
        "engine": "sqlite" if is_sqlite else "postgres",
        "persistent": not is_sqlite,
        "host": host,
    }


@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    [Admin] System-wide activity counters for the dashboard overview:
    total scans, active medications, active reminders, and assistant
    lookups. Counts only — no per-user data is exposed.
    """
    async def count(model, *conditions) -> int:
        query = select(func.count()).select_from(model)
        for cond in conditions:
            query = query.where(cond)
        result = await db.execute(query)
        return int(result.scalar_one() or 0)

    return {
        "scans": await count(ScanHistory),
        "medications": await count(Medication, Medication.is_active.is_(True)),
        "reminders": await count(Reminder, Reminder.is_active.is_(True)),
        "queries": await count(UserQuery),
    }


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        pattern=r"^(PENDING|APPROVED|REJECTED)$",
        description="Filter by approval status",
    ),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """[Admin] List users, newest first, optionally filtered by approval status."""
    query = select(User)
    if status_filter:
        query = query.where(User.status == status_filter)
    query = query.order_by(User.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def update_user_status(
    user_id: UUID,
    request: UpdateUserStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """[Admin] Approve, reject, or reset a user's approval status."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Don't let an admin lock themselves out of their own admin account.
    if user.id == admin.id and request.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own approval status.",
        )

    user.status = request.status
    await db.flush()
    await db.refresh(user)
    return user
