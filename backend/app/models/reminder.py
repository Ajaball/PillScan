"""
Reminder Model
Stores medication reminder schedules and notification preferences.
"""

import uuid
from datetime import datetime, time
from sqlalchemy import String, Boolean, DateTime, Time, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False)
    days_of_week: Mapped[dict | None] = mapped_column(
        JSON, nullable=True  # e.g., [0,1,2,3,4,5,6] for every day; null = daily
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notification_body: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snooze_minutes: Mapped[int] = mapped_column(default=10, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="reminders")
    medication = relationship("Medication", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder(id={self.id}, time={self.reminder_time})>"
