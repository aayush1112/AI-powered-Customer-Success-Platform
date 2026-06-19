from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_role
from app.enums import InteractionType, UserRole
from app.models.user import User
from app.schemas.customer import PaginatedResponse
from app.schemas.interaction import (
    InteractionCreate,
    InteractionCreateResponse,
    InteractionListParams,
    InteractionResponse,
    InteractionUpdate,
    InteractionUpdateResponse,
)
from app.services.cache import CacheKeyBuilder, CacheTTL, cache_service
from app.services.interaction_service import InteractionService

router = APIRouter(prefix="/interactions", tags=["Interactions"])


def _svc(db: AsyncSession = Depends(get_db)) -> InteractionService:
    return InteractionService(db)


async def _invalidate_interaction(interaction_id: uuid.UUID, customer_id: uuid.UUID | None = None) -> None:
    """Clear interaction-related and downstream dashboard cache entries."""
    await cache_service.delete(CacheKeyBuilder.interaction_key(interaction_id))
    if customer_id:
        await cache_service.delete(CacheKeyBuilder.customer_timeline_key(customer_id))
    await cache_service.delete_pattern("dashboard:*")


@router.post("/", response_model=InteractionCreateResponse, status_code=201)
async def create_interaction(
    data: InteractionCreate,
    current_user: User = require_role(UserRole.ADMIN, UserRole.MANAGER),
    service: InteractionService = Depends(_svc),
) -> InteractionCreateResponse:
    """Create an interaction. ADMIN and MANAGER only."""
    interaction = await service.create(data, created_by=current_user.id)
    await cache_service.delete(CacheKeyBuilder.customer_timeline_key(data.customer_id))
    await cache_service.delete_pattern("dashboard:*")
    return InteractionCreateResponse(data=InteractionResponse.model_validate(interaction))


@router.get("/", response_model=PaginatedResponse[InteractionResponse])
async def list_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="Search title and notes"),
    customer_id: uuid.UUID | None = Query(None),
    interaction_type: InteractionType | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    created_by: uuid.UUID | None = Query(None),
    sort_by: str = Query("meeting_date"),
    sort_order: str = Query("desc"),
    _user: User = Depends(get_current_active_user),
    service: InteractionService = Depends(_svc),
) -> PaginatedResponse[InteractionResponse]:
    """List interactions with search, filter, sort, and pagination."""
    params = InteractionListParams(
        page=page,
        page_size=page_size,
        search=search,
        customer_id=customer_id,
        interaction_type=interaction_type,
        start_date=start_date,
        end_date=end_date,
        created_by=created_by,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await service.get_paginated(params)


@router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(
    interaction_id: uuid.UUID,
    _user: User = Depends(get_current_active_user),
    service: InteractionService = Depends(_svc),
) -> InteractionResponse:
    """Get interaction details. All roles."""
    cache_key = CacheKeyBuilder.interaction_key(interaction_id)
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    interaction = await service.get_by_id(interaction_id)
    response = InteractionResponse.model_validate(interaction)
    await cache_service.set_json(cache_key, response.model_dump(mode="json"), ttl=CacheTTL.INTERACTION_DETAIL)
    return response


@router.put("/{interaction_id}", response_model=InteractionUpdateResponse)
async def update_interaction(
    interaction_id: uuid.UUID,
    data: InteractionUpdate,
    current_user: User = require_role(UserRole.ADMIN, UserRole.MANAGER),
    service: InteractionService = Depends(_svc),
) -> InteractionUpdateResponse:
    """Update an interaction. ADMIN and MANAGER only."""
    interaction = await service.update(interaction_id, data)
    response = InteractionResponse.model_validate(interaction)
    await _invalidate_interaction(
        interaction_id,
        customer_id=interaction.customer_id if hasattr(interaction, "customer_id") else None,
    )
    return InteractionUpdateResponse(data=response)
