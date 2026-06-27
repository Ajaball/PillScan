"""
Drug Models
Stores drug information, images, side effects, and contraindications.
Designed for bilingual (Arabic/English) content.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Drug(Base):
    __tablename__ = "drugs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Drug identification
    name_en: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    generic_name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generic_name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Regulatory codes
    ndc_code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    sfda_reg_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Physical characteristics (for manual search)
    shape: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    imprint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scoring: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Drug information
    dosage_form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_instructions_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_instructions_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requires_prescription: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI model class mapping
    model_class_id: Mapped[int | None] = mapped_column(nullable=True, index=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    images = relationship("DrugImage", back_populates="drug", cascade="all, delete-orphan")
    side_effects = relationship("DrugSideEffect", back_populates="drug", cascade="all, delete-orphan")
    contraindications = relationship("DrugContraindication", back_populates="drug", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="drug")
    scan_results = relationship("ScanHistory", back_populates="identified_drug")

    def __repr__(self) -> str:
        return f"<Drug(id={self.id}, name_en={self.name_en})>"


class DrugImage(Base):
    __tablename__ = "drug_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    drug_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="reference"  # 'reference' | 'consumer'
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    drug = relationship("Drug", back_populates="images")


class DrugSideEffect(Base):
    __tablename__ = "drug_side_effects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    drug_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False
    )
    effect_en: Mapped[str] = mapped_column(String(500), nullable=False)
    effect_ar: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="mild"  # 'mild' | 'moderate' | 'severe'
    )

    # Relationships
    drug = relationship("Drug", back_populates="side_effects")


class DrugContraindication(Base):
    __tablename__ = "drug_contraindications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    drug_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False
    )
    contraindication_en: Mapped[str] = mapped_column(String(500), nullable=False)
    contraindication_ar: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relationships
    drug = relationship("Drug", back_populates="contraindications")
