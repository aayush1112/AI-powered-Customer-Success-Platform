# AI-Powered Customer Success Platform

A production-grade, full-stack platform for managing customer relationships, logging interactions, and surfacing AI-generated insights powered by **Google Gemini**.

---

## Features

| Module | Capabilities |
|--------|-------------|
| **Authentication** | JWT auth (access + refresh tokens), bcrypt passwords, RBAC (ADMIN / MANAGER / VIEWER) |
| **Customer Management** | Full CRUD, paginated list, search, filter by status, sort |
| **Interaction Tracking** | Log calls, emails, meetings, notes per customer; timeline view |
| **AI Insights** | Gemini-powered analysis of interactions: summary, sentiment, action items, risks |
| **Dashboard Analytics** | KPI cards, customer status distribution, interaction volume chart, sentiment breakdown |
| **Redis Caching** | Cache-aside pattern on all read-heavy endpoints; 5-minute TTL for dashboard metrics |
| **Admin User Management** | ADMIN-only: view, filter, activate/deactivate, change role for all platform users |
| **Observability** | Structured JSON logs (structlog), correlation IDs, request tracing, 3 health endpoints |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15 · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Redux Toolkit · RTK Query |
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **AI** | Google Gemini (`gemini-2.5-flash`) |
| **DevOps** | Docker · Docker Compose · GitHub Actions · Nginx |
| **Testing** | pytest · pytest-asyncio · httpx · Jest · Testing Library · Playwright |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                Next.js 15 Frontend (React 19)                │
│   RTK Query · Redux · shadcn/ui · Tailwind CSS               │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS REST API
┌───────────────────────────▼──────────────────────────────────┐
│                  FastAPI (Python 3.12)                       │
│   SQLAlchemy 2.0 · structlog · SlowAPI · Pydantic v2         │
└──────────┬────────────────┬───────────────────┬──────────────┘
           │                │                   │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌─────────▼────────┐
    │ PostgreSQL  │  │   Redis 7   │  │  Google Gemini   │
    │     16      │  │  (Cache)    │  │   AI API         │
    └─────────────┘  └─────────────┘  └──────────────────┘
```

For detailed documentation see:
- [Architecture Overview](docs/01-architecture-overview.md)
- [Backend Architecture](docs/02-backend-architecture.md)
- [Frontend Architecture](docs/03-frontend-architecture.md)
- [Database Design](docs/04-database-design.md)
- [Authentication Flow](docs/05-authentication-flow.md)
- [Redis Caching Strategy](docs/06-redis-caching-strategy.md)
- [AI Insight Workflow](docs/07-ai-insight-workflow.md)
- [Dashboard Analytics](docs/08-dashboard-analytics-flow.md)
- [Deployment Guide](docs/09-deployment-guide.md)
- [Troubleshooting Guide](docs/10-troubleshooting-guide.md)

---

## Project Structure

```
.
├── backend/               FastAPI application (Python 3.12)
│   ├── app/
│   │   ├── api/           Routers and dependency injection
│   │   ├── core/          Config, security, logging, rate limiting
│   │   ├── db/            SQLAlchemy engine + async session
│   │   ├── middleware/    HTTP middleware (logging, security headers)
│   │   ├── models/        ORM models (User, Customer, Interaction, AiInsight)
│   │   ├── repositories/  Data access layer
│   │   ├── schemas/       Pydantic schemas (request/response)
│   │   ├── services/      Business logic + AI + cache
│   │   └── exceptions/    Custom exception hierarchy + handlers
│   ├── alembic/           Database migrations
│   └── tests/             pytest test suite (unit + integration)
├── frontend/              Next.js 15 application (TypeScript)
│   └── src/
│       ├── app/           Next.js App Router pages + layouts
│       ├── components/    Shared UI components
│       ├── features/      Feature-scoped modules (auth, customers, admin…)
│       └── services/      RTK Query API slices
├── deployment/            Production docker-compose + nginx config
├── docs/                  Architecture and operational documentation
├── e2e/                   Playwright end-to-end tests
├── scripts/               Setup, test runner, and utility scripts
└── .github/workflows/     CI/CD pipelines (CI, PR validation, main build, release)
```

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 4.x
- A [Google Gemini API key](https://aistudio.google.com/) (free tier available)

### 1 — Configure environment

```bash
# Copy and fill in each .env file
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

**Minimum required changes in `backend/.env`:**

```bash
# Generate a strong secret key
SECRET_KEY=$(openssl rand -hex 32)

# Add your Gemini API key
GEMINI_API_KEY=your_key_here
```

### 2 — One-command startup

**Linux / macOS:**
```bash
chmod +x scripts/setup.sh && ./scripts/setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
```

**Manual:**
```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

### 3 — Access the platform

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/api/v1/docs |
| **Health** | http://localhost:8000/api/v1/health |
| **Liveness** | http://localhost:8000/api/v1/liveness |
| **Readiness** | http://localhost:8000/api/v1/readiness |

### 4 — Create your first admin account

Register via the UI at `http://localhost:3000/register`, then promote to ADMIN via the database:

```bash
docker compose exec postgres psql -U csp_user -d csp_db \
  -c "UPDATE users SET role='ADMIN' WHERE email='your@email.com';"
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Start only the infrastructure (Postgres + Redis)
docker compose up postgres redis -d

# Apply migrations
alembic upgrade head

# Start dev server with hot reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

---

## Environment Variables

### Root `.env` (consumed by docker-compose)

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `csp_db` | Database name |
| `POSTGRES_USER` | `csp_user` | Database user |
| `POSTGRES_PASSWORD` | — | **Required in production** |
| `REDIS_PASSWORD` | — | **Required in production** |
| `BACKEND_PORT` | `8000` | Host port for backend |
| `FRONTEND_PORT` | `3000` | Host port for frontend |

### `backend/.env`

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | **Required** — JWT signing secret (min 32 chars) |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `REDIS_URL` | `redis://...` | Redis connection string |
| `GEMINI_API_KEY` | `""` | Google Gemini API key |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS allowed origins (JSON array) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | JWT access token lifetime |

### `frontend/.env.local`

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |
| `NEXT_PUBLIC_APP_NAME` | `Customer Success Platform` | App display name |

---

## Database Migrations

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Create a new migration (after model changes)
docker compose exec backend alembic revision --autogenerate -m "describe change"

# Rollback one step
docker compose exec backend alembic downgrade -1

# Check current migration version
docker compose exec backend alembic current
```

---

## Running Tests

### Backend tests

```bash
# All tests with coverage report
docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

# Unit tests only (no DB/Redis needed)
cd backend
pytest tests/unit/ -v

# Specific test file
pytest tests/test_customers.py -v
```

### Frontend tests

```bash
cd frontend

# Run Jest tests
npm test

# With coverage
npm run test:coverage

# TypeScript type check
npm run type-check

# ESLint
npm run lint
```

### End-to-end tests (Playwright)

```bash
# Start the full stack first, then:
npx playwright test

# With UI browser
npx playwright test --headed

# Specific spec
npx playwright test e2e/auth.spec.ts
```

---

## CI/CD

Three GitHub Actions workflows:

| Workflow | Trigger | Jobs |
|----------|---------|------|
| [`ci.yml`](.github/workflows/ci.yml) | Push to `main`/`develop`, PRs | Backend lint + tests, Frontend lint + tests, Docker builds, E2E |
| [`pr-validation.yml`](.github/workflows/pr-validation.yml) | Pull requests | Quality gates + coverage + E2E (non-blocking) |
| [`main-build.yml`](.github/workflows/main-build.yml) | Push to `main` | Build + push Docker images to GHCR, smoke test |
| [`release.yml`](.github/workflows/release.yml) | Tag `v*.*.*` | Versioned images, source archive, GitHub Release |

Coverage threshold: **85%** (backend). CI fails if coverage drops below this.

---

## API Documentation

FastAPI auto-generates interactive documentation:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

All endpoints require a Bearer token except `/auth/register`, `/auth/login`, and the health endpoints.

---

## Production Deployment

See [Deployment Guide](docs/09-deployment-guide.md) for full instructions.

**Quick production start:**

```bash
# Build production images
docker compose -f deployment/docker-compose.production.yml build

# Start (requires TLS certs in deployment/nginx/certs/)
docker compose -f deployment/docker-compose.production.yml up -d

# Run migrations
docker compose -f deployment/docker-compose.production.yml exec backend alembic upgrade head
```

**Recommended cloud platforms:**
- **DigitalOcean** — simplest; Droplet + Managed Postgres + Managed Redis (~$60/month)
- **AWS ECS** — production-grade; Fargate + RDS + ElastiCache (~$150/month)
- **Azure Container Apps** — scales to zero (~$80/month)

---

## Security

- Passwords hashed with bcrypt (random salt)
- JWTs signed with HS256 + separate `type` claim to prevent token substitution
- Rate limiting on all endpoints (stricter on auth routes)
- Security headers on both frontend and backend: HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- CORS whitelist — only listed origins are allowed
- Non-root users in all Docker containers
- Secrets validated at startup — weak defaults rejected

---

## Contributing

1. Fork and create a feature branch from `develop`
2. Make changes following the existing patterns
3. Run the full test suite: `pytest tests/` and `npm test`
4. Ensure `ruff check .` and `npm run lint` pass
5. Open a PR — the `pr-validation` workflow runs automatically

---

## License

MIT License — see `LICENSE` for details.
