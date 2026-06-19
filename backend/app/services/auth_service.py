from __future__ import annotations

import uuid

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.enums import UserRole
from app.exceptions.base import ConflictException, UnauthorizedException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.redis_service import redis_service


def _refresh_key(user_id: uuid.UUID) -> str:
    return f"user:{user_id}:refresh_token"


class AuthService:
    """Handles all authentication and token lifecycle operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    # ── Registration ──────────────────────────────────────────────────────────

    async def register_user(self, data: RegisterRequest) -> User:
        """Create a new account with default MANAGER role."""
        if await self._repo.email_exists(data.email.lower()):
            raise ConflictException("An account with this email already exists")

        return await self._repo.create(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role=UserRole.MANAGER,
        )

    # ── Login ─────────────────────────────────────────────────────────────────

    async def authenticate_user(self, data: LoginRequest) -> User:
        """Verify credentials. Uses identical error messages to prevent enumeration."""
        _INVALID = "Invalid email or password"
        user = await self._repo.get_by_email(data.email.lower())
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException(_INVALID)
        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")
        return user

    # ── Token management ──────────────────────────────────────────────────────

    def _claims(self, user: User) -> dict[str, str]:
        return {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }

    def build_token_pair(self, user: User) -> TokenResponse:
        claims = self._claims(user)
        return TokenResponse(
            access_token=create_access_token(claims),
            refresh_token=create_refresh_token(claims),
        )

    async def save_refresh_token(self, user_id: uuid.UUID, token: str) -> None:
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        await redis_service.set(_refresh_key(user_id), token, expire=ttl_seconds)

    async def validate_refresh_token(self, user_id: uuid.UUID, token: str) -> bool:
        """Return True only if the token matches the one stored in Redis."""
        stored = await redis_service.get(_refresh_key(user_id))
        return stored == token

    async def revoke_refresh_token(self, user_id: uuid.UUID) -> None:
        await redis_service.delete(_refresh_key(user_id))

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """Validate a refresh token and issue a new access token and refresh token."""
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedException("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Provided token is not a refresh token")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Malformed token payload")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise UnauthorizedException("Malformed token payload")

        if not await self.validate_refresh_token(user_id, refresh_token):
            raise UnauthorizedException("Refresh token has been revoked")

        user = await self._repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        claims = self._claims(user)
        new_access_token = create_access_token(claims)
        new_refresh_token = create_refresh_token(claims)
        
        await self.save_refresh_token(user_id, new_refresh_token)

        return new_access_token, new_refresh_token

    async def logout(self, user_id: uuid.UUID) -> None:
        """Invalidate the stored refresh token so it cannot be reused."""
        await self.revoke_refresh_token(user_id)
