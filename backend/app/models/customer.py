from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.enums import CustomerStatus

if TYPE_CHECKING:
    from app.models.interaction import Interaction
    from app.models.user import User


class Customer(BaseModel):
    """A company / account managed by the customer success team."""

    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_company_name", "company_name"),
        Index("ix_customers_status", "status"),
        Index("ix_customers_created_by", "created_by"),
        Index("ix_customers_is_deleted", "is_deleted"),
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[CustomerStatus] = mapped_column(
        SAEnum(CustomerStatus, name="customerstatus", create_type=False),
        nullable=False,
        default=CustomerStatus.PROSPECT,
        server_default=CustomerStatus.PROSPECT.value,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Soft delete: preserves interaction history and audit trail.
    # Hard-purge endpoint can be added later for GDPR compliance (admin only).
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────
    created_by_user: Mapped[User | None] = relationship(
        "User",
        back_populates="customers",
        foreign_keys=[created_by],
        lazy="raise_on_sql",
    )
    interactions: Mapped[list[Interaction]] = relationship(
        "Interaction",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="raise_on_sql",
    )

    def __repr__(self) -> str:
        return (
            f"<Customer(id={self.id!r}, company={self.company_name!r}, "
            f"status={self.status!r})>"
        )
