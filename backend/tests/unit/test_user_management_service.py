"""Unit tests for UserManagementService — repository is fully mocked."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.enums import UserRole
from app.exceptions.base import ConflictException, NotFoundException
from app.schemas.user import UserListParams, UserUpdateRequest
from app.services.user_management_service import UserManagementService


@pytest.fixture
def service() -> UserManagementService:
    svc = UserManagementService(MagicMock())
    svc._repo = MagicMock()
    svc._repo.get_by_id = AsyncMock()
    svc._repo.update = AsyncMock()
    svc._repo.get_paginated = AsyncMock()
    svc._repo.count_active_admins = AsyncMock()
    return svc


def _make_user(
    *,
    role: UserRole = UserRole.MANAGER,
    is_active: bool = True,
    user_id: uuid.UUID | None = None,
) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.role = role
    user.is_active = is_active
    user.first_name = "Test"
    user.last_name = "User"
    user.email = "test@example.com"
    user.created_at = MagicMock()
    return user


@pytest.fixture
def admin_user() -> MagicMock:
    return _make_user(role=UserRole.ADMIN)


# ── list_users ────────────────────────────────────────────────────────────────


class TestListUsers:
    async def test_returns_paginated_response(self, service):
        user = _make_user()
        service._repo.get_paginated.return_value = ([user], 1)
        result = await service.list_users(UserListParams())
        assert result.total == 1
        assert result.page == 1
        assert result.pages == 1

    async def test_pagination_math(self, service):
        users = [_make_user() for _ in range(3)]
        service._repo.get_paginated.return_value = (users, 25)
        result = await service.list_users(UserListParams(page=1, page_size=10))
        assert result.pages == 3

    async def test_search_param_forwarded(self, service):
        service._repo.get_paginated.return_value = ([], 0)
        await service.list_users(UserListParams(search="alice"))
        call_kwargs = service._repo.get_paginated.call_args.kwargs
        assert call_kwargs["search"] == "alice"

    async def test_role_filter_forwarded(self, service):
        service._repo.get_paginated.return_value = ([], 0)
        await service.list_users(UserListParams(role=UserRole.ADMIN))
        call_kwargs = service._repo.get_paginated.call_args.kwargs
        assert call_kwargs["role"] == UserRole.ADMIN

    async def test_empty_result_returns_one_page(self, service):
        service._repo.get_paginated.return_value = ([], 0)
        result = await service.list_users(UserListParams())
        assert result.pages == 1
        assert result.items == []


# ── get_user ──────────────────────────────────────────────────────────────────


class TestGetUser:
    async def test_returns_user_response_when_found(self, service):
        user = _make_user()
        service._repo.get_by_id.return_value = user
        result = await service.get_user(user.id)
        assert str(result.id) == str(user.id)

    async def test_raises_404_when_not_found(self, service):
        service._repo.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await service.get_user(uuid.uuid4())

    async def test_correct_id_passed_to_repo(self, service):
        uid = uuid.uuid4()
        service._repo.get_by_id.return_value = _make_user(user_id=uid)
        await service.get_user(uid)
        service._repo.get_by_id.assert_called_once_with(uid)


# ── update_user ───────────────────────────────────────────────────────────────


class TestUpdateUser:
    async def test_happy_path_role_change(self, service, admin_user):
        target = _make_user(role=UserRole.VIEWER)
        service._repo.get_by_id.return_value = target
        service._repo.update.return_value = target
        await service.update_user(
            target.id, UserUpdateRequest(role=UserRole.MANAGER), admin_user
        )
        service._repo.update.assert_called_once_with(target, role=UserRole.MANAGER)

    async def test_happy_path_deactivation(self, service, admin_user):
        target = _make_user(role=UserRole.MANAGER)
        service._repo.get_by_id.return_value = target
        service._repo.update.return_value = target
        await service.update_user(
            target.id, UserUpdateRequest(is_active=False), admin_user
        )
        service._repo.update.assert_called_once_with(target, is_active=False)

    async def test_raises_404_when_user_not_found(self, service, admin_user):
        service._repo.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await service.update_user(uuid.uuid4(), UserUpdateRequest(role=UserRole.MANAGER), admin_user)

    async def test_raises_conflict_on_self_role_downgrade(self, service):
        uid = uuid.uuid4()
        current = _make_user(role=UserRole.ADMIN, user_id=uid)
        target = _make_user(role=UserRole.ADMIN, user_id=uid)
        service._repo.get_by_id.return_value = target
        with pytest.raises(ConflictException, match="downgrade"):
            await service.update_user(uid, UserUpdateRequest(role=UserRole.MANAGER), current)

    async def test_raises_conflict_deactivating_last_admin(self, service, admin_user):
        target = _make_user(role=UserRole.ADMIN)
        service._repo.get_by_id.return_value = target
        service._repo.count_active_admins.return_value = 1
        with pytest.raises(ConflictException, match="last active ADMIN"):
            await service.update_user(
                target.id, UserUpdateRequest(is_active=False), admin_user
            )

    async def test_allows_deactivation_when_multiple_admins(self, service, admin_user):
        target = _make_user(role=UserRole.ADMIN)
        service._repo.get_by_id.return_value = target
        service._repo.count_active_admins.return_value = 2
        service._repo.update.return_value = target
        await service.update_user(
            target.id, UserUpdateRequest(is_active=False), admin_user
        )
        service._repo.update.assert_called_once()

    async def test_raises_conflict_removing_last_admin_role(self, service, admin_user):
        target = _make_user(role=UserRole.ADMIN, is_active=True)
        service._repo.get_by_id.return_value = target
        service._repo.count_active_admins.return_value = 1
        with pytest.raises(ConflictException, match="last active ADMIN"):
            await service.update_user(
                target.id, UserUpdateRequest(role=UserRole.MANAGER), admin_user
            )

    async def test_no_update_call_when_empty_payload(self, service, admin_user):
        target = _make_user()
        service._repo.get_by_id.return_value = target
        await service.update_user(target.id, UserUpdateRequest(), admin_user)
        service._repo.update.assert_not_called()

    async def test_non_admin_role_change_not_blocked_for_other_user(self, service, admin_user):
        target = _make_user(role=UserRole.VIEWER)
        service._repo.get_by_id.return_value = target
        service._repo.update.return_value = target
        await service.update_user(
            target.id, UserUpdateRequest(role=UserRole.MANAGER), admin_user
        )
        service._repo.update.assert_called_once()
