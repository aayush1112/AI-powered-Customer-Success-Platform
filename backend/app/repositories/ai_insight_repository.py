from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import SentimentType
from app.models.ai_insight import AIInsight
from app.repositories.base import BaseRepository


class AIInsightRepository(BaseRepository[AIInsight]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AIInsight, session)

    async def get_by_interaction_id(self, interaction_id: UUID) -> AIInsight | None:
        """Fetch the insight for a given interaction (one-to-one)."""
        stmt = select(AIInsight).where(AIInsight.interaction_id == interaction_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def insight_exists_for_interaction(self, interaction_id: UUID) -> bool:
        """Return True if an insight has already been generated for this interaction."""
        stmt = select(AIInsight.id).where(AIInsight.interaction_id == interaction_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def upsert(
        self,
        interaction_id: UUID,
        *,
        summary: str,
        sentiment: SentimentType,
        action_items: list[str],
        risks: list[str],
    ) -> AIInsight:
        """Create a new insight or replace the existing one for this interaction.

        Uses a fetch-then-write strategy.  The unique constraint on
        interaction_id guarantees at most one row per interaction.
        """
        existing = await self.get_by_interaction_id(interaction_id)
        if existing is not None:
            return await self.update(
                existing,
                summary=summary,
                sentiment=sentiment,
                action_items=action_items,
                risks=risks,
                generated_at=datetime.now(timezone.utc),
            )
        return await self.create(
            interaction_id=interaction_id,
            summary=summary,
            sentiment=sentiment,
            action_items=action_items,
            risks=risks,
        )

    async def get_by_sentiment(
        self,
        sentiment: SentimentType,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AIInsight]:
        """Return insights filtered by AI-assessed sentiment, newest first."""
        stmt = (
            select(AIInsight)
            .where(AIInsight.sentiment == sentiment)
            .order_by(AIInsight.generated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
