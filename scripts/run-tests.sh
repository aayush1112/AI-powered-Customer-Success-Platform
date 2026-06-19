#!/usr/bin/env bash
# run-tests.sh — run all test suites (backend + frontend + E2E)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "======================================================"
echo "  Customer Success Platform — Full Test Suite"
echo "======================================================"

"$SCRIPT_DIR/run-backend-tests.sh"
"$SCRIPT_DIR/run-frontend-tests.sh"

echo ""
echo "======================================================"
echo "  All test suites passed."
echo "======================================================"
