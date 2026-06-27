"""
Medication Model
Represents a user's personal medication — links a user to a drug
with custom dosage, frequency, and schedule information.
"""

import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Boolean, DateTime, Date, Time, Text, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drug_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drugs.id", ondelete="SET NULL"), nullable=True
    )
    # User-customizable fields
    custom_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str] = mapped_column(
        String(50), nullable=False, default="daily"
        # 'once_daily' | 'twice_daily' | 'three_times_daily' | 'weekly' | 'custom'
    )
    times_per_day: Mapped[list | None] = mapped_column(JSON, nullable=True)  # JSON array of times
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="medications")
    drug = relationship("Drug", back_populates="medications")
    reminders = relationship("Reminder", back_populates="medication", cascade="all, delete-orphan")
    adherence_logs = relationship("AdherenceLog", back_populates="medication", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Medication(id={self.id}, user_id={self.user_id}, drug_id={self.drug_id})>"
