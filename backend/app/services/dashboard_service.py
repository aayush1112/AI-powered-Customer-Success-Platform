from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard_repository import DashboardRepository
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


class DashboardAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = DashboardRepository(session)

    async def get_metrics(self) -> DashboardMetrics:
        return await self._repo.get_metrics()

    async def get_customer_status_breakdown(self) -> CustomerStatusBreakdown:
        return await self._repo.get_customer_status_breakdown()

    async def get_interaction_trends(
        self, period: DashboardPeriod
    ) -> list[InteractionTrendPoint]:
        return await self._repo.get_interaction_trends(period)

    async def get_interaction_type_breakdown(self) -> InteractionTypeBreakdown:
        return await self._repo.get_interaction_type_breakdown()

    async def get_sentiment_breakdown(self) -> SentimentBreakdown:
        return await self._repo.get_sentiment_breakdown()

    async def get_top_risks(self) -> list[RiskItem]:
        return await self._repo.get_top_risks()

    async def get_top_action_items(self) -> list[ActionItem]:
        return await self._repo.get_top_action_items()

    async def get_recent_activity(self) -> list[RecentActivityItem]:
        return await self._repo.get_recent_activity()
