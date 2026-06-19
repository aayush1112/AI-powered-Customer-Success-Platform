from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.enums import UserRole

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.interaction import Interaction


class User(BaseModel):
    """Platform user with role-based access control."""

    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", create_type=False),
        nullable=False,
        default=UserRole.VIEWER,
        server_default=UserRole.VIEWER.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # ── Relationships ────────────────────────────────────────────────
    # lazy="raise_on_sql" prevents accidental synchronous loads in async context;
    # callers must use selectinload() / joinedload() explicitly.
    customers: Mapped[list[Customer]] = relationship(
        "Customer",
        back_populates="created_by_user",
        foreign_keys="Customer.created_by",
        lazy="raise_on_sql",
    )
    interactions: Mapped[list[Interaction]] = relationship(
        "Interaction",
        back_populates="created_by_user",
        foreign_keys="Interaction.created_by",
        lazy="raise_on_sql",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email={self.email!r}, role={self.role!r})>"
