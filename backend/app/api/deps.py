from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.enums import UserRole
from app.exceptions.base import ForbiddenException, UnauthorizedException
from app.models.user import User
from app.repositories.user_repository import UserRepository

# auto_error=False so we can return a clean 401 instead of FastAPI's default 403
_bearer = HTTPBearer(auto_error=False)


# ── Database session ──────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession; commit on success, rollback on exception."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Auth dependencies ─────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and verify the Bearer token; return the matching User."""
    if not credentials:
        raise UnauthorizedException("Not authenticated")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedException("Could not validate credentials")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Invalid token payload")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid token payload")

    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise UnauthorizedException("User not found")
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Extend get_current_user with an is_active guard."""
    if not current_user.is_active:
        raise UnauthorizedException("Account is deactivated")
    return current_user


def require_role(*roles: UserRole) -> Depends:
    """Dependency factory for role-based access control.

    Usage:
        @router.get("/admin")
        async def admin_route(user: User = require_role(UserRole.ADMIN)):
            ...

        @router.get("/admin-or-manager")
        async def mixed_route(user: User = require_role(UserRole.ADMIN, UserRole.MANAGER)):
            ...
    """

    async def _check(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in roles:
            allowed = [r.value for r in roles]
            raise ForbiddenException(
                f"Insufficient permissions. Requires one of: {allowed}"
            )
        return current_user

    return Depends(_check)
