# Database Design

## PostgreSQL 16 — Schema Overview

All tables use UUID primary keys, UTC timestamps with timezone, and soft-delete semantics where applicable.

---

## Entity Relationship Diagram

```
┌─────────────────────────┐
│          users          │
│─────────────────────────│
│ id          UUID   PK   │
│ first_name  VARCHAR     │◄──────────────┐
│ last_name   VARCHAR     │               │
│ email       VARCHAR UQ  │    created_by FK (future)
│ hashed_pw   VARCHAR     │               │
│ role        ENUM        │               │
│ is_active   BOOLEAN     │               │
│ created_at  TIMESTAMPTZ │               │
│ updated_at  TIMESTAMPTZ │               │
└─────────────────────────┘               │
                                          │
┌─────────────────────────┐               │
│        customers        │               │
│─────────────────────────│               │
│ id            UUID PK   │               │
│ company_name  VARCHAR   │               │
│ industry      VARCHAR   │               │
│ contact_name  VARCHAR   │               │
│ contact_email VARCHAR   │               │
│ contact_phone VARCHAR?  │               │
│ status        ENUM      │               │
│ created_at    TIMESTAMPTZ               │
│ updated_at    TIMESTAMPTZ               │
└────────────┬────────────┘               │
             │ 1                          │
             │ n                          │
┌────────────▼────────────┐               │
│      interactions       │               │
│─────────────────────────│               │
│ id              UUID PK │               │
│ customer_id     UUID FK │               │
│ type            ENUM    │               │
│ subject         VARCHAR │               │
│ notes           TEXT    │               │
│ occurred_at     TIMESTAMPTZ             │
│ created_at      TIMESTAMPTZ             │
│ updated_at      TIMESTAMPTZ             │
└────────────┬────────────┘               │
             │ 1                          │
             │ 0..1                       │
┌────────────▼────────────┐               │
│       ai_insights       │               │
│─────────────────────────│               │
│ id              UUID PK │               │
│ interaction_id  UUID FK │               │
│ summary         TEXT    │               │
│ sentiment       ENUM    │               │
│ action_items    JSON    │               │
│ risks           JSON    │               │
│ generated_at    TIMESTAMPTZ             │
└─────────────────────────┘               │
                                          │
```

---

## Table Definitions

### `users`

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    hashed_pw   VARCHAR(255) NOT NULL,
    role        user_role_enum NOT NULL DEFAULT 'VIEWER',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Indexes:**
- `UNIQUE (email)` — enforced by DB constraint
- Index on `role` and `is_active` for admin listing queries

**Enum `user_role`:** `ADMIN`, `MANAGER`, `VIEWER`

---

### `customers`

```sql
CREATE TABLE customers (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name   VARCHAR(255) NOT NULL,
    industry       VARCHAR(100),
    contact_name   VARCHAR(255) NOT NULL,
    contact_email  VARCHAR(255) NOT NULL,
    contact_phone  VARCHAR(50),
    status         customer_status_enum NOT NULL DEFAULT 'PROSPECT',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Enum `customer_status`:** `PROSPECT`, `ACTIVE`, `AT_RISK`, `CHURNED`

**Indexes:**
- Index on `status` for dashboard aggregation queries
- Index on `company_name` for search (ilike)

---

### `interactions`

```sql
CREATE TABLE interactions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id  UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    type         interaction_type_enum NOT NULL,
    subject      VARCHAR(500) NOT NULL,
    notes        TEXT,
    occurred_at  TIMESTAMPTZ NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Enum `interaction_type`:** `CALL`, `EMAIL`, `MEETING`, `NOTE`

**Indexes:**
- Index on `customer_id` for per-customer interaction queries
- Index on `occurred_at DESC` for timeline ordering

---

### `ai_insights`

```sql
CREATE TABLE ai_insights (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id  UUID NOT NULL UNIQUE REFERENCES interactions(id) ON DELETE CASCADE,
    summary         TEXT NOT NULL,
    sentiment       sentiment_type_enum NOT NULL,
    action_items    JSONB NOT NULL DEFAULT '[]',
    risks           JSONB NOT NULL DEFAULT '[]',
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Enum `sentiment_type`:** `POSITIVE`, `NEUTRAL`, `NEGATIVE`

**Notes:**
- `UNIQUE (interaction_id)` — one insight per interaction; regeneration replaces the existing record
- `JSONB` for `action_items` and `risks` allows flexible, queryable arrays

---

## Migration Management

Migrations are managed by **Alembic**. All migrations live in `backend/alembic/versions/`.

```bash
# Create a new migration
alembic revision --autogenerate -m "describe the change"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history --verbose
```

`alembic/env.py` uses the same `DATABASE_URL` from `Settings` to ensure migrations target the correct database.

---

## Connection Pooling

SQLAlchemy `create_async_engine` is configured with:
- `pool_size=10` — steady-state connections kept open
- `max_overflow=20` — burst connections allowed beyond pool_size
- `pool_pre_ping=True` — validates connections before checkout (detects stale connections after DB restart)

For production deployments with high concurrency, consider PgBouncer as a connection pooler in front of PostgreSQL.

---

## Backup Strategy (Recommendations)

| Frequency | Method | Retention |
|-----------|--------|-----------|
| Continuous | PostgreSQL WAL archiving to S3 | 7 days |
| Daily | `pg_dump` logical backup | 30 days |
| Weekly | Full volume snapshot (cloud provider) | 12 weeks |

Point-in-time recovery (PITR) is recommended for production environments.
