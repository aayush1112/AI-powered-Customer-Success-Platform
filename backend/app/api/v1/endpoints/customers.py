from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_role
from app.enums import CustomerStatus, UserRole
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerCreateResponse,
    CustomerListParams,
    CustomerResponse,
    CustomerUpdate,
    CustomerUpdateResponse,
    PaginatedResponse,
)
from app.schemas.interaction import CustomerTimelineResponse
from app.services.cache import CacheKeyBuilder, CacheTTL, cache_service
from app.services.customer_service import CustomerService
from app.services.interaction_service import InteractionService

router = APIRouter(prefix="/customers", tags=["Customers"])


def _svc(db: AsyncSession = Depends(get_db)) -> CustomerService:
    return CustomerService(db)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _invalidate_customer(customer_id: uuid.UUID) -> None:
    """Remove all cache entries that must be fresh after a customer write."""
    await cache_service.delete(CacheKeyBuilder.customer_key(customer_id))
    await cache_service.delete(CacheKeyBuilder.customer_timeline_key(customer_id))
    await cache_service.delete_pattern("customers:list:*")
    await cache_service.delete_pattern("dashboard:*")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=CustomerCreateResponse, status_code=201)
async def create_customer(
    data: CustomerCreate,
    current_user: User = require_role(UserRole.ADMIN, UserRole.MANAGER),
    service: CustomerService = Depends(_svc),
) -> CustomerCreateResponse:
    """Create a new customer. ADMIN and MANAGER only."""
    customer = await service.create(data, created_by=current_user.id)
    await cache_service.delete_pattern("customers:list:*")
    await cache_service.delete_pattern("dashboard:*")
    return CustomerCreateResponse(data=CustomerResponse.model_validate(customer))


@router.get("/", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None, description="Search across company name, contact name, and email"),
    status: CustomerStatus | None = Query(None),
    industry: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    _user: User = Depends(get_current_active_user),
    service: CustomerService = Depends(_svc),
) -> PaginatedResponse[CustomerResponse]:
    """List customers with optional search, filter, sort, and pagination."""
    cache_key = CacheKeyBuilder.customer_list_key(
        page, page_size, search,
        status.value if status else None,
        industry, sort_by, sort_order,
    )
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    params = CustomerListParams(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        industry=industry,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    result = await service.get_paginated(params)
    await cache_service.set_json(cache_key, result.model_dump(mode="json"), ttl=CacheTTL.CUSTOMER_LIST)
    return result


@router.get("/{customer_id}/timeline", response_model=CustomerTimelineResponse)
async def get_customer_timeline(
    customer_id: uuid.UUID,
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerTimelineResponse:
    """Get the chronological interaction timeline for a customer. All roles."""
    cache_key = CacheKeyBuilder.customer_timeline_key(customer_id)
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    service = InteractionService(db)
    result = await service.get_customer_timeline(customer_id)
    await cache_service.set_json(cache_key, result.model_dump(mode="json"), ttl=CacheTTL.CUSTOMER_DETAIL)
    return result


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    _user: User = Depends(get_current_active_user),
    service: CustomerService = Depends(_svc),
) -> CustomerResponse:
    """Retrieve a single customer by ID. All roles."""
    cache_key = CacheKeyBuilder.customer_key(customer_id)
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    customer = await service.get_by_id(customer_id)
    response = CustomerResponse.model_validate(customer)
    await cache_service.set_json(cache_key, response.model_dump(mode="json"), ttl=CacheTTL.CUSTOMER_DETAIL)
    return response


@router.put("/{customer_id}", response_model=CustomerUpdateResponse)
async def update_customer(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    current_user: User = require_role(UserRole.ADMIN, UserRole.MANAGER),
    service: CustomerService = Depends(_svc),
) -> CustomerUpdateResponse:
    """Update customer fields. ADMIN and MANAGER only."""
    customer = await service.update(customer_id, data)
    await _invalidate_customer(customer_id)
    return CustomerUpdateResponse(data=CustomerResponse.model_validate(customer))


@router.delete("/{customer_id}", status_code=204, response_model=None)
async def delete_customer(
    customer_id: uuid.UUID,
    _user: User = require_role(UserRole.ADMIN),
    service: CustomerService = Depends(_svc),
) -> None:
    """Soft-delete a customer. ADMIN only."""
    await service.delete(customer_id)
    await _invalidate_customer(customer_id)
