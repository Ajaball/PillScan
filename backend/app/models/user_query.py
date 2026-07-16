"""
User Query History Model
Stores each drug-assistant lookup a user makes, so they can see their past
searches. Linked to the user (registration) table by a foreign key.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserQuery(Base):
    __tablename__ = "user_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    # Foreign key to the registration (users) table. Cascade-delete so a user's
    # history is removed with the account.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The drug name the user searched for.
    query_text: Mapped[str] = mapped_column(String(120), nullable=False)
    # Whether the assistant recognised the drug for this query.
    recognized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # The structured result (name, sideEffects, usageTimes) as returned. Nullable
    # so a not-configured / errored query is still recorded.
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationship back to the user (registration) table.
    user = relationship("User", back_populates="queries")

    def __repr__(self) -> str:
        return f"<UserQuery(id={self.id}, user_id={self.user_id}, q={self.query_text!r})>"
