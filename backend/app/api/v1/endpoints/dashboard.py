from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.enums import UserRole
from app.models.user import User
from app.schemas.dashboard import (
    ActionItem,
    CustomerStatusBreakdown,
    DashboardMetrics,
    DashboardPeriod,
    InteractionTrendPoint,
    InteractionTypeBreakdown,
    RecentActivityItem,
    RiskItem,
    SentimentBreakdown,
)
from app.services.cache import CacheKeyBuilder, CacheTTL, cache_service
from app.services.dashboard_service import DashboardAnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_any_role = require_role(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER)


# ── Helper ────────────────────────────────────────────────────────────────────

async def _cached(key: str, ttl: int, svc_coro):  # type: ignore[type-arg]
    """Generic cache-aside helper for dashboard endpoints.

    Checks Redis first; on a miss calls *svc_coro* (an awaitable), caches the
    serialised result, and returns the original Pydantic object / list.
    """
    cached = await cache_service.get_json(key)
    if cached is not None:
        return cached

    result = await svc_coro
    if hasattr(result, "model_dump"):
        serializable = result.model_dump(mode="json")
    elif isinstance(result, list):
        serializable = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in result
        ]
    else:
        serializable = result

    await cache_service.set_json(key, serializable, ttl=ttl)
    return result


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> DashboardMetrics:
    return await _cached(
        CacheKeyBuilder.dashboard_key("metrics"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_metrics(),
    )


@router.get("/customer-status", response_model=CustomerStatusBreakdown)
async def get_customer_status(
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> CustomerStatusBreakdown:
    return await _cached(
        CacheKeyBuilder.dashboard_key("customer-status"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_customer_status_breakdown(),
    )


@router.get("/interactions", response_model=list[InteractionTrendPoint])
async def get_interaction_trends(
    period: DashboardPeriod = DashboardPeriod.LAST_30_DAYS,
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> list[InteractionTrendPoint]:
    return await _cached(
        CacheKeyBuilder.dashboard_key(f"interaction-trends:{period.value}"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_interaction_trends(period),
    )


@router.get("/interaction-types", response_model=InteractionTypeBreakdown)
async def get_interaction_types(
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> InteractionTypeBreakdown:
    return await _cached(
        CacheKeyBuilder.dashboard_key("interaction-types"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_interaction_type_breakdown(),
    )


@router.get("/sentiment", response_model=SentimentBreakdown)
async def get_sentiment(
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> SentimentBreakdown:
    return await _cached(
        CacheKeyBuilder.dashboard_key("sentiment"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_sentiment_breakdown(),
    )


@router.get("/risks", response_model=list[RiskItem])
async def get_risks(
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> list[RiskItem]:
    return await _cached(
        CacheKeyBuilder.dashboard_key("risks"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_top_risks(),
    )


@router.get("/action-items", response_model=list[ActionItem])
async def get_action_items(
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> list[ActionItem]:
    return await _cached(
        CacheKeyBuilder.dashboard_key("action-items"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_top_action_items(),
    )


@router.get("/recent-activity", response_model=list[RecentActivityItem])
async def get_recent_activity(
    _user: User = _any_role,
    db: AsyncSession = Depends(get_db),
) -> list[RecentActivityItem]:
    return await _cached(
        CacheKeyBuilder.dashboard_key("recent-activity"),
        CacheTTL.DASHBOARD,
        DashboardAnalyticsService(db).get_recent_activity(),
    )
