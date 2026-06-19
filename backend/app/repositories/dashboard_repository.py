from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import SentimentType
from app.models.ai_insight import AIInsight
from app.models.customer import Customer
from app.models.interaction import Interaction
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


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_metrics(self) -> DashboardMetrics:
        # Customer counts by status (one round trip)
        status_rows = await self._session.execute(
            select(Customer.status, func.count().label("cnt"))
            .where(Customer.is_deleted.is_(False))
            .group_by(Customer.status)
        )
        status_data: dict[str, int] = {}
        for row in status_rows:
            status_data[row.status.value] = row.cnt

        # Total interactions
        total_iact = await self._session.execute(
            select(func.count()).select_from(Interaction)
        )
        total_interactions: int = total_iact.scalar_one()

        # Interactions this calendar month
        month_iact = await self._session.execute(
            select(func.count())
            .select_from(Interaction)
            .where(
                func.date_trunc("month", Interaction.meeting_date)
                == func.date_trunc("month", func.now())
            )
        )
        interactions_this_month: int = month_iact.scalar_one()

        # Sentiment counts (one round trip)
        sentiment_rows = await self._session.execute(
            select(AIInsight.sentiment, func.count().label("cnt"))
            .group_by(AIInsight.sentiment)
        )
        sentiment_data: dict[str, int] = {}
        for row in sentiment_rows:
            sentiment_data[row.sentiment.value] = row.cnt

        return DashboardMetrics(
            total_customers=sum(status_data.values()),
            active_customers=status_data.get("ACTIVE", 0),
            at_risk_customers=status_data.get("AT_RISK", 0),
            churned_customers=status_data.get("CHURNED", 0),
            total_interactions=total_interactions,
            interactions_this_month=interactions_this_month,
            positive_insights=sentiment_data.get("POSITIVE", 0),
            neutral_insights=sentiment_data.get("NEUTRAL", 0),
            negative_insights=sentiment_data.get("NEGATIVE", 0),
        )

    async def get_customer_status_breakdown(self) -> CustomerStatusBreakdown:
        rows = await self._session.execute(
            select(Customer.status, func.count().label("cnt"))
            .where(Customer.is_deleted.is_(False))
            .group_by(Customer.status)
        )
        data: dict[str, int] = {row.status.value: row.cnt for row in rows}
        return CustomerStatusBreakdown(
            ACTIVE=data.get("ACTIVE", 0),
            AT_RISK=data.get("AT_RISK", 0),
            CHURNED=data.get("CHURNED", 0),
            PROSPECT=data.get("PROSPECT", 0),
        )

    async def get_interaction_trends(
        self, period: DashboardPeriod
    ) -> list[InteractionTrendPoint]:
        day_col = func.date_trunc("day", Interaction.meeting_date)
        stmt = (
            select(day_col.label("day"), func.count().label("cnt"))
            .group_by(day_col)
            .order_by(day_col)
        )

        period_days = {
            DashboardPeriod.LAST_7_DAYS: 7,
            DashboardPeriod.LAST_30_DAYS: 30,
            DashboardPeriod.LAST_90_DAYS: 90,
        }
        if period in period_days:
            cutoff = datetime.now(timezone.utc) - timedelta(days=period_days[period])
            stmt = stmt.where(Interaction.meeting_date >= cutoff)

        rows = await self._session.execute(stmt)
        return [
            InteractionTrendPoint(date=row.day.strftime("%Y-%m-%d"), count=row.cnt)
            for row in rows
        ]

    async def get_interaction_type_breakdown(self) -> InteractionTypeBreakdown:
        rows = await self._session.execute(
            select(Interaction.interaction_type, func.count().label("cnt"))
            .group_by(Interaction.interaction_type)
        )
        data: dict[str, int] = {row.interaction_type.value: row.cnt for row in rows}
        return InteractionTypeBreakdown(
            MEETING=data.get("MEETING", 0),
            CALL=data.get("CALL", 0),
            EMAIL=data.get("EMAIL", 0),
            QBR=data.get("QBR", 0),
        )

    async def get_sentiment_breakdown(self) -> SentimentBreakdown:
        rows = await self._session.execute(
            select(AIInsight.sentiment, func.count().label("cnt"))
            .group_by(AIInsight.sentiment)
        )
        data: dict[str, int] = {row.sentiment.value: row.cnt for row in rows}
        return SentimentBreakdown(
            POSITIVE=data.get("POSITIVE", 0),
            NEUTRAL=data.get("NEUTRAL", 0),
            NEGATIVE=data.get("NEGATIVE", 0),
        )

    async def get_top_risks(self, limit: int = 10) -> list[RiskItem]:
        stmt = text(
            """
            SELECT value AS risk, COUNT(*) AS cnt
            FROM ai_insights,
                 jsonb_array_elements_text(risks) AS value
            WHERE jsonb_array_length(risks) > 0
            GROUP BY value
            ORDER BY cnt DESC
            LIMIT :limit
            """
        )
        rows = await self._session.execute(stmt, {"limit": limit})
        return [RiskItem(risk=row.risk, count=row.cnt) for row in rows]

    async def get_top_action_items(self, limit: int = 10) -> list[ActionItem]:
        stmt = text(
            """
            SELECT value AS action, COUNT(*) AS cnt
            FROM ai_insights,
                 jsonb_array_elements_text(action_items) AS value
            WHERE jsonb_array_length(action_items) > 0
            GROUP BY value
            ORDER BY cnt DESC
            LIMIT :limit
            """
        )
        rows = await self._session.execute(stmt, {"limit": limit})
        return [ActionItem(action=row.action, count=row.cnt) for row in rows]

    async def get_recent_activity(self, limit_each: int = 5) -> list[RecentActivityItem]:
        items: list[RecentActivityItem] = []

        # Recent customers
        cust_rows = await self._session.execute(
            select(Customer.company_name, Customer.status, Customer.created_at)
            .where(Customer.is_deleted.is_(False))
            .order_by(Customer.created_at.desc())
            .limit(limit_each)
        )
        for row in cust_rows:
            items.append(
                RecentActivityItem(
                    type="customer",
                    title=row.company_name,
                    subtitle=f"Status: {row.status.value}",
                    timestamp=row.created_at.isoformat(),
                )
            )

        # Recent interactions
        int_rows = await self._session.execute(
            select(Interaction.title, Interaction.interaction_type, Interaction.meeting_date)
            .order_by(Interaction.meeting_date.desc())
            .limit(limit_each)
        )
        for row in int_rows:
            items.append(
                RecentActivityItem(
                    type="interaction",
                    title=row.title,
                    subtitle=row.interaction_type.value,
                    timestamp=row.meeting_date.isoformat(),
                )
            )

        # Recent insights (joined with interactions for context)
        ins_rows = await self._session.execute(
            select(
                Interaction.title.label("interaction_title"),
                AIInsight.sentiment,
                AIInsight.generated_at,
            )
            .join(Interaction, AIInsight.interaction_id == Interaction.id)
            .order_by(AIInsight.generated_at.desc())
            .limit(limit_each)
        )
        for row in ins_rows:
            items.append(
                RecentActivityItem(
                    type="insight",
                    title=f'AI Insight: "{row.interaction_title}"',
                    subtitle=f"{row.sentiment.value} sentiment",
                    timestamp=row.generated_at.isoformat(),
                )
            )

        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[:10]
