from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.enums import InteractionType

if TYPE_CHECKING:
    from app.models.ai_insight import AIInsight
    from app.models.customer import Customer
    from app.models.user import User


class Interaction(BaseModel):
    """A recorded touchpoint between the CSM team and a customer."""

    __tablename__ = "interactions"
    __table_args__ = (
        Index("ix_interactions_customer_id", "customer_id"),
        Index("ix_interactions_meeting_date", "meeting_date"),
        Index("ix_interactions_created_by", "created_by"),
        Index("ix_interactions_interaction_type", "interaction_type"),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    interaction_type: Mapped[InteractionType] = mapped_column(
        SAEnum(InteractionType, name="interactiontype", create_type=False),
        nullable=False,
    )
    meeting_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────
    customer: Mapped[Customer] = relationship(
        "Customer",
        back_populates="interactions",
        lazy="raise_on_sql",
    )
    created_by_user: Mapped[User | None] = relationship(
        "User",
        back_populates="interactions",
        foreign_keys=[created_by],
        lazy="raise_on_sql",
    )
    ai_insight: Mapped[AIInsight | None] = relationship(
        "AIInsight",
        back_populates="interaction",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="raise_on_sql",
    )

    def __repr__(self) -> str:
        return (
            f"<Interaction(id={self.id!r}, type={self.interaction_type!r}, "
            f"customer_id={self.customer_id!r})>"
        )
