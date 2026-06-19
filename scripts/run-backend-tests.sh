#!/usr/bin/env bash
# run-backend-tests.sh — run backend pytest suite with coverage
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$(cd "$SCRIPT_DIR/../backend" && pwd)"

echo ""
echo "────────────────────────────────────────────────────"
echo "  Backend Tests (pytest)"
echo "────────────────────────────────────────────────────"

# Ensure services are reachable
if ! command -v pg_isready &>/dev/null; then
  echo "[warn] pg_isready not found — skipping DB health check"
else
  pg_isready -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" || {
    echo "[error] PostgreSQL not ready. Start it with: docker compose up postgres -d"
    exit 1
  }
fi

cd "$BACKEND"

# Install dev deps if not present
if ! python -c "import pytest" &>/dev/null; then
  echo "Installing dev dependencies..."
  pip install -r requirements-dev.txt
fi

echo ""
echo "Running unit tests..."
python -m pytest tests/unit/ -v --tb=short -q

echo ""
echo "Running integration tests..."
python -m pytest tests/integration/ -v --tb=short -q

echo ""
echo "Running API tests (full suite)..."
python -m pytest tests/ -v --tb=short \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov

echo ""
echo "[backend] All tests passed."
