from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.services.redis_service import redis_service

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", summary="Health check", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Returns the aggregate health status of the API and its dependencies.

    Checks PostgreSQL connectivity and Redis connectivity. Returns `degraded`
    if any dependency is unreachable; individual service statuses are listed
    under `services`.
    """
    services: dict[str, str] = {}

    # ── Database ─────────────────────────────────────────────
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as exc:
        logger.error("Database health check failed", error=str(exc))
        services["database"] = "unhealthy"

    # ── Redis ────────────────────────────────────────────────
    try:
        ok = await redis_service.ping()
        services["redis"] = "healthy" if ok else "unhealthy"
    except Exception as exc:
        logger.error("Redis health check failed", error=str(exc))
        services["redis"] = "unhealthy"

    overall = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": services,
    }


@router.get("/readiness", summary="Readiness probe", tags=["Health"])
async def readiness_check(response: Response, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Kubernetes / load-balancer readiness probe.

    Returns HTTP 200 only when the application is ready to serve traffic
    (database and Redis both reachable). Returns HTTP 503 when degraded.
    Suitable for use as a `readinessProbe` in Kubernetes or as an ELB
    health-check target.
    """
    checks: dict[str, bool] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        logger.warning("Readiness: database unavailable", error=str(exc))
        checks["database"] = False

    try:
        checks["redis"] = bool(await redis_service.ping())
    except Exception as exc:
        logger.warning("Readiness: redis unavailable", error=str(exc))
        checks["redis"] = False

    ready = all(checks.values())
    if not ready:
        response.status_code = 503

    return {
        "ready": ready,
        "checks": {k: "ok" if v else "fail" for k, v in checks.items()},
    }


@router.get("/liveness", summary="Liveness probe", tags=["Health"])
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe.

    Returns HTTP 200 as long as the process is running and the event loop is
    responsive. Does NOT check external dependencies — those belong in the
    readiness probe. If this endpoint fails, the container should be restarted.
    """
    return {"alive": True, "version": settings.APP_VERSION}
