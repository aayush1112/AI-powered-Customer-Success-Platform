"""add soft delete to customers

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-18

Design decision: soft delete over hard delete because:
  - Customers link to Interactions (Phase 5). Hard delete cascades and wipes all
    meeting notes and AI insights — an irreversible loss of data.
  - Audit trail is preserved for compliance and historical reporting.
  - A GDPR hard-purge endpoint (ADMIN only) can be added later without changing
    the normal delete flow.
  - Restoring an accidentally deleted customer requires only flipping is_deleted.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "customers",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_customers_is_deleted", "customers", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_customers_is_deleted", table_name="customers")
    op.drop_column("customers", "deleted_at")
    op.drop_column("customers", "is_deleted")
