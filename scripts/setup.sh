#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  Project setup script — Linux / macOS
# ─────────────────────────────────────────────────────────────
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO] $*${NC}"; }
success() { echo -e "${GREEN}[OK]   $*${NC}"; }
warn()    { echo -e "${YELLOW}[WARN] $*${NC}"; }

info "Setting up AI-Powered Customer Success Platform..."

# ── Prerequisites ─────────────────────────────────────────────
command -v docker &>/dev/null \
  || { echo "Docker not found. Install Docker Desktop first."; exit 1; }
(docker compose version &>/dev/null || docker-compose version &>/dev/null) \
  || { echo "Docker Compose not found."; exit 1; }

# ── Environment files ─────────────────────────────────────────
if [[ ! -f ".env" ]]; then
  cp .env.example .env
  warn "Created .env — update secrets before running in production."
fi
if [[ ! -f "backend/.env" ]]; then
  cp backend/.env.example backend/.env
  warn "Created backend/.env — update secrets before running in production."
fi
if [[ ! -f "frontend/.env.local" ]]; then
  cp frontend/.env.example frontend/.env.local
  warn "Created frontend/.env.local."
fi

# ── Build & start ─────────────────────────────────────────────
info "Building and starting Docker services..."
docker compose up --build -d

info "Waiting for services to be healthy (up to 60 s)..."
for i in $(seq 1 12); do
  if docker compose exec backend curl -sf http://localhost:8000/api/v1/health &>/dev/null; then
    break
  fi
  sleep 5
done

# ── Migrations ────────────────────────────────────────────────
info "Running database migrations..."
docker compose exec backend alembic upgrade head

success "Setup complete!"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/api/v1/docs"
echo "  Health:   http://localhost:8000/api/v1/health"
