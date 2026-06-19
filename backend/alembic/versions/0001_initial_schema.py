"""Initial schema: users, customers, interactions, ai_insights

Creates all four core tables with PostgreSQL enum types, indexes,
foreign-key constraints, and JSONB columns.

Revision ID: 0001
Revises:
Create Date: 2026-06-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ─────────────────────────────────────────────────────
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── 1. PostgreSQL native enum types ──────────────────────────────────────
    # Must be created before any table that references them.
    # Using raw SQL so Alembic does not attempt to manage them as table columns.
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'VIEWER')")
    op.execute(
        "CREATE TYPE customerstatus AS ENUM ('ACTIVE', 'AT_RISK', 'CHURNED', 'PROSPECT')"
    )
    op.execute(
        "CREATE TYPE interactiontype AS ENUM ('MEETING', 'CALL', 'EMAIL', 'QBR')"
    )
    op.execute(
        "CREATE TYPE sentimenttype AS ENUM ('POSITIVE', 'NEUTRAL', 'NEGATIVE')"
    )

    # ── 2. users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            # create_type=False: enum type was created above via raw SQL
            postgresql.ENUM("ADMIN", "MANAGER", "VIEWER", name="userrole", create_type=False),
            nullable=False,
            server_default="VIEWER",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    # Unique index on email — primary lookup for authentication
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── 3. customers ─────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("contact_name", sa.String(200), nullable=False),
        sa.Column("contact_email", sa.String(255), nullable=False),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "ACTIVE", "AT_RISK", "CHURNED", "PROSPECT",
                name="customerstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="PROSPECT",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
        # SET NULL preserves historical customer records when a user is deleted
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_customers_created_by_users",
            ondelete="SET NULL",
        ),
    )
    # company_name: ORDER BY and ILIKE searches on customer list pages
    op.create_index("ix_customers_company_name", "customers", ["company_name"])
    # status: at-risk / churned filter is the core CSP dashboard query
    op.create_index("ix_customers_status", "customers", ["status"])
    # created_by: scopes customer lists to an account manager without a full scan
    op.create_index("ix_customers_created_by", "customers", ["created_by"])

    # ── 4. interactions ───────────────────────────────────────────────────────
    op.create_table(
        "interactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "interaction_type",
            postgresql.ENUM(
                "MEETING", "CALL", "EMAIL", "QBR",
                name="interactiontype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("meeting_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interactions"),
        # CASCADE: deleting a customer removes all its interactions
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name="fk_interactions_customer_id_customers",
            ondelete="CASCADE",
        ),
        # SET NULL: deleting a user keeps interaction history intact
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_interactions_created_by_users",
            ondelete="SET NULL",
        ),
    )
    # customer_id: "load all interactions for a customer" is the most common query
    op.create_index("ix_interactions_customer_id", "interactions", ["customer_id"])
    # meeting_date: date-range queries for timeline and calendar views
    op.create_index("ix_interactions_meeting_date", "interactions", ["meeting_date"])
    # created_by: filter interactions per account manager
    op.create_index("ix_interactions_created_by", "interactions", ["created_by"])

    # ── 5. ai_insights ────────────────────────────────────────────────────────
    op.create_table(
        "ai_insights",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "interaction_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "sentiment",
            postgresql.ENUM(
                "POSITIVE", "NEUTRAL", "NEGATIVE",
                name="sentimenttype",
                create_type=False,
            ),
            nullable=False,
        ),
        # JSONB: queryable JSON — enables future GIN indexing on action_items / risks
        sa.Column(
            "action_items",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "risks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ai_insights"),
        # Unique constraint enforces one insight per interaction at the DB level
        sa.UniqueConstraint("interaction_id", name="uq_ai_insights_interaction_id"),
        # CASCADE: deleting an interaction removes its insight
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interactions.id"],
            name="fk_ai_insights_interaction_id_interactions",
            ondelete="CASCADE",
        ),
    )
    # interaction_id: primary lookup path for "get insight for this interaction"
    op.create_index(
        "ix_ai_insights_interaction_id",
        "ai_insights",
        ["interaction_id"],
        unique=True,
    )


def downgrade() -> None:
    # Drop tables in reverse FK-dependency order so constraints are satisfied
    op.drop_table("ai_insights")
    op.drop_table("interactions")
    op.drop_table("customers")
    op.drop_table("users")

    # Drop enum types only after all tables that reference them are gone
    op.execute("DROP TYPE IF EXISTS sentimenttype")
    op.execute("DROP TYPE IF EXISTS interactiontype")
    op.execute("DROP TYPE IF EXISTS customerstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
