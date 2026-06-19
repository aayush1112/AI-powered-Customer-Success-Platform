# AI-Powered Customer Success Platform

A production-grade, full-stack platform for managing customer relationships and surfacing AI-generated insights.

## Tech Stack

| Layer      | Technology                                          |
|------------|-----------------------------------------------------|
| Frontend   | Next.js 15 · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Redux Toolkit · RTK Query |
| Backend    | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Alembic    |
| Database   | PostgreSQL 16                                        |
| Cache      | Redis 7                                              |
| DevOps     | Docker · Docker Compose · GitHub Actions             |

## Project Structure

```
.
├── backend/          # FastAPI application
├── frontend/         # Next.js 15 application
├── infrastructure/   # IaC & deployment configs (future)
├── docs/             # Architecture & API docs
├── scripts/          # Setup & utility scripts
└── .github/          # CI/CD workflows
```

## Quick Start

### Prerequisites
- Docker Desktop ≥ 4.x
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### 1 — Clone & configure environment

```bash
git clone <repo-url>
cd customer-success-platform

# Copy and edit environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Edit each `.env` file with your own secrets before proceeding.

### 2 — One-command Docker startup

**Linux / macOS:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
```

### 3 — Manual startup (alternative)

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

### 4 — Verify

| Service  | URL                                      |
|----------|------------------------------------------|
| Frontend | http://localhost:3000                    |
| Backend  | http://localhost:8000                    |
| API Docs | http://localhost:8000/api/v1/openapi.json |
| Health   | http://localhost:8000/api/v1/health      |

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# Start Postgres & Redis via Docker only
docker compose up postgres redis -d

# Run dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Database Migrations

```bash
# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback one step
docker compose exec backend alembic downgrade -1
```

## Testing

```bash
# Backend
docker compose exec backend pytest tests/ -v --cov=app

# Frontend
cd frontend && npm run type-check
```

## Implementation Phases

- **Phase 1 (current)** — Project foundation, infrastructure, health checks
- **Phase 2** — Authentication & RBAC
- **Phase 3** — Customer & Interaction management
- **Phase 4** — AI Insights & Dashboard analytics
- **Phase 5** — Production hardening & observability
