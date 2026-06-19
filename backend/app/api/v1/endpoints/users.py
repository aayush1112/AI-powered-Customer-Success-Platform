from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.customer import PaginatedResponse
from app.schemas.user import UserListParams, UserUpdateRequest
from app.services.user_management_service import UserManagementService

router = APIRouter(prefix="/users", tags=["Users"])


def _svc(db: AsyncSession = Depends(get_db)) -> UserManagementService:
    return UserManagementService(db)


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    role: UserRole | None = Query(None),
    is_active: bool | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    _user: User = require_role(UserRole.ADMIN),
    service: UserManagementService = Depends(_svc),
) -> PaginatedResponse[UserResponse]:
    """List all users with pagination, search, and filters. ADMIN only."""
    params = UserListParams(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await service.list_users(params)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    _user: User = require_role(UserRole.ADMIN),
    service: UserManagementService = Depends(_svc),
) -> UserResponse:
    """Retrieve a single user by ID. ADMIN only."""
    return await service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdateRequest,
    current_user: User = require_role(UserRole.ADMIN),
    service: UserManagementService = Depends(_svc),
) -> UserResponse:
    """Update user role and/or active status. ADMIN only."""
    return await service.update_user(user_id, data, current_user)
