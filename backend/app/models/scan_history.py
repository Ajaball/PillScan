"""
Scan History Model
Records every pill scan performed by a user, including AI predictions.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identified_drug_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drugs.id", ondelete="SET NULL"), nullable=True
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    all_predictions: Mapped[dict | None] = mapped_column(
        JSON, nullable=True  # Top-5 predictions with confidence scores
    )
    inference_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="cloud"  # 'cloud' | 'on_device'
    )
    inference_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", back_populates="scan_history")
    identified_drug = relationship("Drug", back_populates="scan_results")

    def __repr__(self) -> str:
        return f"<ScanHistory(id={self.id}, confidence={self.confidence_score})>"
