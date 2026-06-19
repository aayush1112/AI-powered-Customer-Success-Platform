from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import SentimentType
from app.models.ai_insight import AIInsight
from app.repositories.ai_insight_repository import AIInsightRepository
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.ai_insight import (
    AIInsightGenerateResponse,
    AIInsightResponse,
    GeminiInsightOutput,
)
from app.services.ai.gemini_client import GeminiClient
from app.services.ai.prompts import build_insight_prompt

logger = structlog.get_logger()


class AIInsightService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AIInsightRepository(session)
        self._interaction_repo = InteractionRepository(session)
        self._gemini = GeminiClient()

    # ── Core generation ───────────────────────────────────────────────────────

    async def generate(
        self, interaction_id: uuid.UUID
    ) -> AIInsightGenerateResponse:
        """Generate (or replace) an AI insight for *interaction_id*.

        Always returns a 201-ready response:
        - On Gemini success → stores and returns real insight.
        - On any Gemini failure → stores and returns the fallback insight
          and sets is_fallback=True so the caller can surface it.
        """
        interaction = await self._interaction_repo.get_with_relations(interaction_id)
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")

        notes = interaction.notes or ""
        prompt = build_insight_prompt(notes)

        logger.info("insight_generation_start", interaction_id=str(interaction_id))

        raw = await self._gemini.generate_json(prompt)
        validated, is_fallback = self._parse_gemini_output(raw, interaction_id)

        insight = await self._repo.upsert(
            interaction_id=interaction_id,
            summary=validated.summary,
            sentiment=SentimentType(validated.sentiment),
            action_items=validated.action_items,
            risks=validated.risks,
        )

        logger.info(
            "insight_generation_complete",
            interaction_id=str(interaction_id),
            sentiment=validated.sentiment,
            is_fallback=is_fallback,
        )

        return AIInsightGenerateResponse(
            success=True,
            data=AIInsightResponse.model_validate(insight),
            is_fallback=is_fallback,
        )

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_interaction(
        self, interaction_id: uuid.UUID
    ) -> AIInsight:
        """Return the stored insight or raise 404."""
        insight = await self._repo.get_by_interaction_id(interaction_id)
        if not insight:
            raise HTTPException(
                status_code=404,
                detail="No insight found for this interaction. Generate one first.",
            )
        return insight

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_gemini_output(
        self,
        raw: dict | None,
        interaction_id: uuid.UUID,
    ) -> tuple[GeminiInsightOutput, bool]:
        """Validate Gemini JSON dict against GeminiInsightOutput.

        Returns (validated_output, is_fallback).
        Falls back gracefully on None input or schema mismatch.
        """
        if raw is None:
            logger.warning(
                "insight_fallback_activated",
                reason="gemini_returned_none",
                interaction_id=str(interaction_id),
            )
            return GeminiInsightOutput.fallback(), True

        try:
            validated = GeminiInsightOutput.model_validate(raw)
            return validated, False
        except ValidationError as exc:
            logger.warning(
                "insight_fallback_activated",
                reason="gemini_schema_mismatch",
                interaction_id=str(interaction_id),
                validation_errors=str(exc),
            )
            return GeminiInsightOutput.fallback(), True
