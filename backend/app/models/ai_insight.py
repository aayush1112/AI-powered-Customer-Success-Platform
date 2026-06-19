from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums import SentimentType

if TYPE_CHECKING:
    from app.models.interaction import Interaction


class AIInsight(Base):
    """AI-generated analysis for a single customer interaction.

    One-to-one with Interaction. Inherits directly from Base (not BaseModel)
    because it uses generated_at instead of the standard created_at/updated_at
    pair — insights are immutable once generated.
    """

    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    interaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[SentimentType] = mapped_column(
        SAEnum(SentimentType, name="sentimenttype", create_type=False),
        nullable=False,
    )
    # JSONB stores structured lists of action items / risks from the AI model.
    # server_default of empty array prevents NULL on INSERT without explicit value.
    action_items: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="'[]'::jsonb",
    )
    risks: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="'[]'::jsonb",
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────
    interaction: Mapped[Interaction] = relationship(
        "Interaction",
        back_populates="ai_insight",
        lazy="raise_on_sql",
    )

    def __repr__(self) -> str:
        return (
            f"<AIInsight(id={self.id!r}, interaction_id={self.interaction_id!r}, "
            f"sentiment={self.sentiment!r})>"
        )
