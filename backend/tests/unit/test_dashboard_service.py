"""Unit tests for DashboardAnalyticsService — repository is fully mocked."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.dashboard import (
    CustomerStatusBreakdown,
    DashboardMetrics,
    DashboardPeriod,
    InteractionTrendPoint,
    InteractionTypeBreakdown,
    SentimentBreakdown,
)
from app.services.dashboard_service import DashboardAnalyticsService


@pytest.fixture
def service() -> DashboardAnalyticsService:
    svc = DashboardAnalyticsService(MagicMock())
    svc._repo = MagicMock()
    svc._repo.get_metrics = AsyncMock()
    svc._repo.get_customer_status_breakdown = AsyncMock()
    svc._repo.get_interaction_trends = AsyncMock()
    svc._repo.get_interaction_type_breakdown = AsyncMock()
    svc._repo.get_sentiment_breakdown = AsyncMock()
    svc._repo.get_top_risks = AsyncMock()
    svc._repo.get_top_action_items = AsyncMock()
    svc._repo.get_recent_activity = AsyncMock()
    return svc


class TestGetMetrics:
    async def test_delegates_to_repo_and_returns_result(self, service):
        expected = MagicMock(spec=DashboardMetrics)
        service._repo.get_metrics.return_value = expected

        result = await service.get_metrics()

        service._repo.get_metrics.assert_called_once_with()
        assert result is expected

    async def test_called_once_per_request(self, service):
        service._repo.get_metrics.return_value = MagicMock()
        await service.get_metrics()
        await service.get_metrics()
        assert service._repo.get_metrics.call_count == 2


class TestGetCustomerStatusBreakdown:
    async def test_delegates_to_repo(self, service):
        expected = MagicMock(spec=CustomerStatusBreakdown)
        service._repo.get_customer_status_breakdown.return_value = expected
        result = await service.get_customer_status_breakdown()
        service._repo.get_customer_status_breakdown.assert_called_once_with()
        assert result is expected


class TestGetInteractionTrends:
    async def test_passes_period_to_repo(self, service):
        service._repo.get_interaction_trends.return_value = []
        await service.get_interaction_trends(DashboardPeriod.LAST_7_DAYS)
        service._repo.get_interaction_trends.assert_called_once_with(DashboardPeriod.LAST_7_DAYS)

    async def test_returns_list(self, service):
        service._repo.get_interaction_trends.return_value = [
            MagicMock(spec=InteractionTrendPoint)
        ]
        result = await service.get_interaction_trends(DashboardPeriod.LAST_30_DAYS)
        assert isinstance(result, list)
        assert len(result) == 1

    async def test_all_periods_forwarded(self, service):
        service._repo.get_interaction_trends.return_value = []
        for period in DashboardPeriod:
            await service.get_interaction_trends(period)
        assert service._repo.get_interaction_trends.call_count == len(list(DashboardPeriod))


class TestGetInteractionTypeBreakdown:
    async def test_delegates_to_repo(self, service):
        expected = MagicMock(spec=InteractionTypeBreakdown)
        service._repo.get_interaction_type_breakdown.return_value = expected
        result = await service.get_interaction_type_breakdown()
        assert result is expected


class TestGetSentimentBreakdown:
    async def test_delegates_to_repo(self, service):
        expected = MagicMock(spec=SentimentBreakdown)
        service._repo.get_sentiment_breakdown.return_value = expected
        result = await service.get_sentiment_breakdown()
        assert result is expected


class TestGetTopRisks:
    async def test_returns_empty_list_when_no_insights(self, service):
        service._repo.get_top_risks.return_value = []
        result = await service.get_top_risks()
        assert result == []

    async def test_delegates_to_repo(self, service):
        risks = [MagicMock(), MagicMock()]
        service._repo.get_top_risks.return_value = risks
        result = await service.get_top_risks()
        assert result is risks


class TestGetTopActionItems:
    async def test_returns_empty_list_when_no_insights(self, service):
        service._repo.get_top_action_items.return_value = []
        result = await service.get_top_action_items()
        assert result == []

    async def test_delegates_to_repo(self, service):
        items = [MagicMock()]
        service._repo.get_top_action_items.return_value = items
        result = await service.get_top_action_items()
        assert result is items


class TestGetRecentActivity:
    async def test_empty_when_no_data(self, service):
        service._repo.get_recent_activity.return_value = []
        result = await service.get_recent_activity()
        assert result == []

    async def test_delegates_to_repo(self, service):
        activity = [MagicMock(), MagicMock(), MagicMock()]
        service._repo.get_recent_activity.return_value = activity
        result = await service.get_recent_activity()
        assert result is activity
