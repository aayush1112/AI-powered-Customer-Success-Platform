from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.exceptions.base import ConflictException, NotFoundException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.customer import PaginatedResponse
from app.schemas.user import UserListParams, UserUpdateRequest


class UserManagementService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def list_users(self, params: UserListParams) -> PaginatedResponse[UserResponse]:
        items, total = await self._repo.get_paginated(
            page=params.page,
            page_size=params.page_size,
            search=params.search,
            role=params.role,
            is_active=params.is_active,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        pages = max(1, (total + params.page_size - 1) // params.page_size)
        return PaginatedResponse(
            items=[UserResponse.model_validate(u) for u in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id: uuid.UUID,
        data: UserUpdateRequest,
        current_user: User,
    ) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        updates = data.model_dump(exclude_none=True)
        if not updates:
            return UserResponse.model_validate(user)

        # Rule 4: Prevent self-role downgrade
        if "role" in updates and str(user.id) == str(current_user.id):
            if updates["role"] != UserRole.ADMIN:
                raise ConflictException("Cannot downgrade your own ADMIN role")

        # Rule 1: Prevent last active ADMIN deactivation
        if updates.get("is_active") is False and user.role == UserRole.ADMIN:
            if await self._repo.count_active_admins() <= 1:
                raise ConflictException("Cannot deactivate the last active ADMIN account")

        # Rule 2: Prevent removing ADMIN role from last active ADMIN
        if (
            "role" in updates
            and user.role == UserRole.ADMIN
            and updates["role"] != UserRole.ADMIN
            and user.is_active
        ):
            if await self._repo.count_active_admins() <= 1:
                raise ConflictException("Cannot change the role of the last active ADMIN")

        updated = await self._repo.update(user, **updates)
        return UserResponse.model_validate(updated)
