#!/usr/bin/env bash
# run-frontend-tests.sh — run Jest unit and component tests
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND="$(cd "$SCRIPT_DIR/../frontend" && pwd)"

echo ""
echo "────────────────────────────────────────────────────"
echo "  Frontend Tests (Jest)"
echo "────────────────────────────────────────────────────"

cd "$FRONTEND"

# Install deps if missing
if [ ! -d "node_modules" ]; then
  echo "Installing npm dependencies..."
  npm ci
fi

echo ""
echo "Running Jest tests with coverage..."
npm run test:coverage

echo ""
echo "[frontend] All tests passed."
