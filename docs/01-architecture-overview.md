# Architecture Overview

## AI-Powered Customer Success Platform

---

## System Summary

The Customer Success Platform (CSP) is a full-stack, AI-augmented application that enables customer success teams to manage customer relationships, log interactions, and receive AI-generated insights powered by Google Gemini. It is structured as three cooperating layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser / Client                        │
│              Next.js 15 — React 19 — TypeScript             │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / REST
┌───────────────────────────▼─────────────────────────────────┐
│                     FastAPI Backend                         │
│         Python 3.12 — SQLAlchemy 2.0 — Alembic             │
│         Structlog — SlowAPI — Redis Cache                   │
└──────┬────────────────────┬────────────────────┬────────────┘
       │                    │                    │
┌──────▼──────┐   ┌─────────▼─────────┐   ┌─────▼────────┐
│ PostgreSQL  │   │    Redis 7         │   │ Google Gemini │
│     16      │   │  (Cache + Session) │   │   AI API      │
└─────────────┘   └───────────────────┘   └──────────────┘
```

---

## Component Roles

| Component        | Role                                                                 |
|-----------------|----------------------------------------------------------------------|
| **Next.js 15**  | Server-rendered React SPA; Auth guard via Edge Middleware; RTK Query |
| **FastAPI**     | REST API; async request handling; JWT auth; business rules           |
| **PostgreSQL 16** | Primary data store; enforces relational constraints                |
| **Redis 7**     | Response cache (TTL-based); token revocation blacklist               |
| **Google Gemini** | AI model that generates customer interaction summaries and insights |

---

## Key Design Principles

1. **Async-first** — FastAPI + SQLAlchemy 2.0 async + asyncpg; the backend never blocks the event loop on I/O.
2. **Layered architecture** — `router → service → repository → model`. No raw SQL in routers; no business logic in repositories.
3. **RBAC at every layer** — JWT `require_role()` dependency on every protected endpoint; middleware auth guard on every protected frontend route.
4. **Cache-aside** — Redis is consulted before database queries for read-heavy endpoints (dashboard, customer lists). Writes always go to the database first, then invalidate the cache.
5. **Structured observability** — All logs are structured JSON in production via structlog, with a correlation `request_id` threaded through every request.
6. **Immutable secrets** — All secrets are environment variables; defaults are rejected at startup by Pydantic validators.

---

## Request Lifecycle

```
Browser ──► Edge Middleware (auth_status cookie check)
         ──► Next.js page / RTK Query fetch
         ──► FastAPI CORS + LoggingMiddleware (assigns request_id)
         ──► SecurityHeadersMiddleware
         ──► SlowAPIMiddleware (rate limit)
         ──► Router (Depends: JWT decode → require_role)
         ──► Service (business rules)
         ──► Repository (SQLAlchemy async query)
         ──► PostgreSQL
         ◄── Response (JSON) ── structlog ── X-Request-ID header
```

---

## Security Layers

| Layer | Mechanism |
|-------|-----------|
| Network | CORS whitelist; Nginx TLS termination in production |
| Transport | HTTPS enforced; HSTS header |
| Authentication | Bearer JWT (access + refresh token pair) |
| Authorization | `require_role(UserRole.*)` FastAPI dependency |
| Frontend guard | Next.js Edge Middleware cookie check + client-side role redirect |
| Rate limiting | SlowAPI (slowapi) per IP; configurable per endpoint |
| Response hardening | X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy |

---

## Data Flow — AI Insight Generation

```
POST /api/v1/insights/generate/{interaction_id}
  └─► Fetch interaction + customer from DB
  └─► Build structured prompt (app.services.ai.prompts)
  └─► Call Gemini API (gemini-2.5-flash) with retry logic
  └─► Parse response JSON → AiInsight model
  └─► Persist to DB
  └─► Invalidate related cache keys
  └─► Return AiInsightResponse
```

---

## Folder Map (top-level)

```
.
├── backend/              FastAPI application (Python)
│   ├── app/
│   │   ├── api/          Routers and dependency injection
│   │   ├── core/         Config, security, logging, rate limiting
│   │   ├── db/           SQLAlchemy engine + session factory
│   │   ├── middleware/   HTTP middleware (logging, security headers)
│   │   ├── models/       ORM models
│   │   ├── repositories/ Data access layer
│   │   ├── schemas/      Pydantic request/response models
│   │   ├── services/     Business logic + AI + cache
│   │   └── exceptions/   Custom exception hierarchy + handlers
│   ├── alembic/          Database migrations
│   └── tests/            pytest test suite
├── frontend/             Next.js 15 application (TypeScript)
│   └── src/
│       ├── app/          Next.js App Router pages + layouts
│       ├── components/   Shared UI components (shadcn/ui)
│       ├── features/     Feature-scoped logic (auth, admin, …)
│       └── services/     RTK Query API slices
├── deployment/           Production docker-compose + nginx config
├── docs/                 Architecture and operational documentation
├── e2e/                  Playwright end-to-end tests
├── scripts/              Setup, test, and utility shell scripts
└── .github/workflows/    CI/CD pipelines
```
