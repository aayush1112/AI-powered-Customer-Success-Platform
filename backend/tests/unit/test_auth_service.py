"""Unit tests for AuthService — all external I/O is mocked."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.base import ConflictException, UnauthorizedException
from app.schemas.auth import LoginRequest, RegisterRequest


def _make_service() -> object:
    """Construct AuthService with mocked repo and redis_service."""
    from app.services.auth_service import AuthService

    with patch("app.services.auth_service.redis_service"):
        svc = AuthService(MagicMock())

    # Replace internal collaborators with controllable mocks
    svc._repo = MagicMock()
    svc._repo.email_exists = AsyncMock(return_value=False)
    svc._repo.create = AsyncMock()
    svc._repo.get_by_email = AsyncMock(return_value=None)
    svc._repo.get_by_id = AsyncMock(return_value=None)
    return svc


@pytest.fixture
def service():
    return _make_service()


@pytest.fixture
def register_data() -> RegisterRequest:
    return RegisterRequest(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="Password123!",
    )


@pytest.fixture
def login_data() -> LoginRequest:
    return LoginRequest(email="john@example.com", password="Password123!")


# ── Registration ──────────────────────────────────────────────────────────────


class TestRegisterUser:
    async def test_raises_conflict_if_email_exists(self, service, register_data):
        service._repo.email_exists.return_value = True
        with pytest.raises(ConflictException):
            await service.register_user(register_data)

    async def test_creates_user_with_manager_role(self, service, register_data):
        from app.enums import UserRole

        mock_user = MagicMock()
        mock_user.role = UserRole.MANAGER
        service._repo.email_exists.return_value = False
        service._repo.create.return_value = mock_user

        result = await service.register_user(register_data)

        service._repo.create.assert_called_once()
        call_kwargs = service._repo.create.call_args.kwargs
        assert call_kwargs["role"] == UserRole.MANAGER
        assert call_kwargs["email"] == register_data.email.lower()
        assert result is mock_user

    async def test_email_is_lowercased(self, service):
        mock_user = MagicMock()
        service._repo.create.return_value = mock_user

        data = RegisterRequest(
            first_name="A",
            last_name="B",
            email="UPPER@EXAMPLE.COM",
            password="Password123!",
        )
        await service.register_user(data)
        assert service._repo.create.call_args.kwargs["email"] == "upper@example.com"

    async def test_password_is_hashed(self, service, register_data):
        service._repo.create.return_value = MagicMock()
        await service.register_user(register_data)
        stored_hash = service._repo.create.call_args.kwargs["password_hash"]
        # bcrypt hashes start with $2b$ or $2a$
        assert stored_hash.startswith("$2")
        assert stored_hash != register_data.password


# ── Authentication ────────────────────────────────────────────────────────────


class TestAuthenticateUser:
    async def test_raises_unauthorized_if_user_not_found(self, service, login_data):
        service._repo.get_by_email.return_value = None
        with pytest.raises(UnauthorizedException):
            await service.authenticate_user(login_data)

    async def test_raises_unauthorized_for_wrong_password(self, service, login_data):
        from app.core.security import hash_password

        user = MagicMock()
        user.password_hash = hash_password("DifferentPass1!")
        user.is_active = True
        service._repo.get_by_email.return_value = user

        with pytest.raises(UnauthorizedException):
            await service.authenticate_user(login_data)

    async def test_raises_unauthorized_if_inactive(self, service, login_data):
        from app.core.security import hash_password

        user = MagicMock()
        user.password_hash = hash_password("Password123!")
        user.is_active = False
        service._repo.get_by_email.return_value = user

        with pytest.raises(UnauthorizedException):
            await service.authenticate_user(login_data)

    async def test_returns_user_on_valid_credentials(self, service, login_data):
        from app.core.security import hash_password

        user = MagicMock()
        user.password_hash = hash_password("Password123!")
        user.is_active = True
        service._repo.get_by_email.return_value = user

        result = await service.authenticate_user(login_data)
        assert result is user


# ── Token pair ────────────────────────────────────────────────────────────────


class TestBuildTokenPair:
    def test_returns_token_response(self, service):
        from app.enums import UserRole
        from app.schemas.auth import TokenResponse

        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "a@b.com"
        user.role = MagicMock()
        user.role.value = UserRole.MANAGER.value

        result = service.build_token_pair(user)
        assert isinstance(result, TokenResponse)
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    def test_access_and_refresh_tokens_differ(self, service):
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "x@y.com"
        user.role = MagicMock()
        user.role.value = "MANAGER"

        pair = service.build_token_pair(user)
        assert pair.access_token != pair.refresh_token


# ── Refresh access token ──────────────────────────────────────────────────────


class TestRefreshAccessToken:
    async def test_invalid_jwt_raises_unauthorized(self, service):
        with pytest.raises(UnauthorizedException):
            await service.refresh_access_token("this.is.not.valid")

    async def test_access_token_used_as_refresh_raises_unauthorized(self, service):
        from app.core.security import create_access_token

        access = create_access_token({"sub": str(uuid.uuid4())})
        with pytest.raises(UnauthorizedException, match="not a refresh token"):
            await service.refresh_access_token(access)

    async def test_revoked_token_raises_unauthorized(self, service):
        from app.core.security import create_refresh_token

        uid = uuid.uuid4()
        token = create_refresh_token({"sub": str(uid)})

        # validate_refresh_token returns False → token revoked
        service.validate_refresh_token = AsyncMock(return_value=False)

        with pytest.raises(UnauthorizedException):
            await service.refresh_access_token(token)

    async def test_valid_token_issues_new_access_token(self, service):
        from app.enums import UserRole
        from app.core.security import create_refresh_token

        uid = uuid.uuid4()
        token = create_refresh_token({"sub": str(uid)})

        user = MagicMock()
        user.id = uid
        user.email = "a@b.com"
        user.role = MagicMock()
        user.role.value = UserRole.MANAGER.value
        user.is_active = True

        service.validate_refresh_token = AsyncMock(return_value=True)
        service._repo.get_by_id.return_value = user

        new_token = await service.refresh_access_token(token)
        assert isinstance(new_token, str)
        assert len(new_token) > 0


# ── Logout ────────────────────────────────────────────────────────────────────


class TestLogout:
    async def test_logout_revokes_token(self, service):
        uid = uuid.uuid4()
        service.revoke_refresh_token = AsyncMock()
        await service.logout(uid)
        service.revoke_refresh_token.assert_called_once_with(uid)
