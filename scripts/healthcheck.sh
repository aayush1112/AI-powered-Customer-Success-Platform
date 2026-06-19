#!/usr/bin/env bash
# ============================================================
# healthcheck.sh — Verify all CSP services are reachable
# Usage: ./scripts/healthcheck.sh [--host HOST] [--port PORT]
# ============================================================
set -euo pipefail

HOST="${HOST:-localhost}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

PASS=0
FAIL=0

check() {
    local name="$1"
    local url="$2"
    local expected="${3:-200}"

    if command -v curl >/dev/null 2>&1; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
    else
        echo "  [SKIP] $name — curl not available"
        return
    fi

    if [ "$STATUS" = "$expected" ]; then
        echo "  [OK]   $name ($url) → HTTP $STATUS"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $name ($url) → HTTP $STATUS (expected $expected)"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "=============================================="
echo " CSP Health Check"
echo " Host: $HOST"
echo "=============================================="
echo ""

echo "Backend services:"
check "Liveness"  "http://$HOST:$BACKEND_PORT/api/v1/liveness"
check "Readiness" "http://$HOST:$BACKEND_PORT/api/v1/readiness"
check "Health"    "http://$HOST:$BACKEND_PORT/api/v1/health"
check "API Docs"  "http://$HOST:$BACKEND_PORT/api/v1/docs"

echo ""
echo "Frontend:"
check "Frontend"  "http://$HOST:$FRONTEND_PORT"

echo ""
echo "----------------------------------------------"
echo " Results: $PASS passed, $FAIL failed"
echo "----------------------------------------------"

if [ "$FAIL" -gt 0 ]; then
    echo " STATUS: UNHEALTHY"
    exit 1
else
    echo " STATUS: HEALTHY"
    exit 0
fi
