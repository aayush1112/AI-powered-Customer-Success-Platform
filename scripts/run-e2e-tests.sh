#!/usr/bin/env bash
# run-e2e-tests.sh — run Playwright end-to-end tests
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo ""
echo "────────────────────────────────────────────────────"
echo "  E2E Tests (Playwright)"
echo "────────────────────────────────────────────────────"

cd "$ROOT"

# Ensure Playwright browsers are installed
if ! npx playwright --version &>/dev/null; then
  echo "Installing Playwright..."
  npm install -D @playwright/test
  npx playwright install --with-deps chromium
fi

PLAYWRIGHT_BASE_URL="${PLAYWRIGHT_BASE_URL:-http://localhost:3000}"

echo "Target: $PLAYWRIGHT_BASE_URL"
echo ""

npx playwright test \
  --reporter=list \
  "$@"

echo ""
echo "[e2e] Playwright tests complete."
echo "View HTML report: npx playwright show-report playwright-report"
