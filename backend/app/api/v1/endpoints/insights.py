from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.enums import UserRole
from app.models.user import User
from app.schemas.ai_insight import AIInsightGenerateResponse, AIInsightResponse
from app.services.ai_insight_service import AIInsightService
from app.services.cache import CacheKeyBuilder, CacheTTL, cache_service

router = APIRouter(prefix="/insights", tags=["Insights"])


async def _invalidate_insight(interaction_id: uuid.UUID) -> None:
    """Remove insight + downstream dashboard cache entries after generation."""
    await cache_service.delete(CacheKeyBuilder.insight_key(interaction_id))
    await cache_service.delete_pattern("dashboard:*")


# ── POST /insights/generate/{interaction_id} ──────────────────────────────────

@router.post(
    "/generate/{interaction_id}",
    response_model=AIInsightGenerateResponse,
    status_code=201,
    summary="Generate an AI insight for an interaction",
)
async def generate_insight(
    interaction_id: uuid.UUID,
    _user: User = require_role(UserRole.ADMIN, UserRole.MANAGER),
    db: AsyncSession = Depends(get_db),
) -> AIInsightGenerateResponse:
    """Analyse the meeting notes of *interaction_id* with Gemini and store the result.
    If an insight already exists it is replaced (upsert).
    Returns the stored insight and an *is_fallback* flag when the AI service was unavailable.
    """
    svc = AIInsightService(db)
    result = await svc.generate(interaction_id)
    await _invalidate_insight(interaction_id)
    return result


# ── GET /insights/{interaction_id} ────────────────────────────────────────────

@router.get(
    "/{interaction_id}",
    response_model=AIInsightResponse,
    summary="Retrieve the AI insight for an interaction",
)
async def get_insight(
    interaction_id: uuid.UUID,
    _user: User = require_role(UserRole.ADMIN, UserRole.MANAGER, UserRole.VIEWER),
    db: AsyncSession = Depends(get_db),
) -> AIInsightResponse:
    """Return the stored AI insight for *interaction_id*, or 404 if none has been generated yet."""
    cache_key = CacheKeyBuilder.insight_key(interaction_id)
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    svc = AIInsightService(db)
    insight = await svc.get_by_interaction(interaction_id)
    response = AIInsightResponse.model_validate(insight)
    await cache_service.set_json(cache_key, response.model_dump(mode="json"), ttl=CacheTTL.AI_INSIGHT)
    return response


# ── POST /insights/regenerate/{interaction_id} ────────────────────────────────

@router.post(
    "/regenerate/{interaction_id}",
    response_model=AIInsightGenerateResponse,
    status_code=200,
    summary="Re-run AI analysis and replace the existing insight",
)
async def regenerate_insight(
    interaction_id: uuid.UUID,
    _user: User = require_role(UserRole.ADMIN, UserRole.MANAGER),
    db: AsyncSession = Depends(get_db),
) -> AIInsightGenerateResponse:
    """Force a fresh Gemini analysis regardless of whether an insight already exists."""
    svc = AIInsightService(db)
    result = await svc.generate(interaction_id)
    await _invalidate_insight(interaction_id)
    return result
