"""add index on interactions.interaction_type

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-18

Design decision: No soft delete for Interaction rows.
  - The Interaction model has no is_deleted / deleted_at columns.
  - Adding them would require a data migration and schema change.
  - The spec says "implement soft delete if architecture already supports it".
  - Since the current architecture does not support it for Interaction, delete
    functionality is intentionally omitted from Phase 5. A future migration can
    add soft delete if the business requires it (e.g. Phase 6 cleanup tooling).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_interactions_interaction_type",
        "interactions",
        ["interaction_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_interactions_interaction_type", table_name="interactions")
