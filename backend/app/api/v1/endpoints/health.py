from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.services.redis_service import redis_service

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", summary="Health check", response_model=None)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Returns the health status of the API and its upstream dependencies.

    Response shape:
    ```json
    {
      "status": "healthy",
      "version": "0.1.0",
      "environment": "development",
      "services": {
        "database": "healthy",
        "redis": "healthy"
      }
    }
    ```
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
