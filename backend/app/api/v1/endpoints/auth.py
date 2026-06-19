from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.exceptions.base import UnauthorizedException
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

_COOKIE_NAME = "refresh_token"
_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response: Response, token: str, is_production: bool) -> None:
    """Set the refresh token as an httpOnly cookie.

    Token storage decision:
    - httpOnly=True prevents JavaScript access (XSS mitigation)
    - secure=True (production) ensures HTTPS-only transmission
    - samesite="lax" prevents CSRF on cross-site navigations
    - path="/" allows Next.js middleware to read the cookie flag

    In a same-origin deployment (Nginx reverse proxy) this is the recommended
    approach. For cross-origin development the token is also returned in the
    JSON response body so the frontend can store it in localStorage as a fallback.
    """
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@limiter.limit("3/minute")
@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Register a new user account",
)
async def register(
    request: Request,
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterResponse:
    await AuthService(db).register_user(payload)
    return RegisterResponse()


@limiter.limit("5/minute")
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    from app.core.config import settings

    service = AuthService(db)
    user = await service.authenticate_user(payload)
    tokens = service.build_token_pair(user)
    await service.save_refresh_token(user.id, tokens.refresh_token)

    # Set httpOnly cookie and also return token in body for cross-origin clients
    _set_refresh_cookie(
        response,
        tokens.refresh_token,
        is_production=settings.ENVIRONMENT == "production",
    )
    return tokens


@limiter.limit("20/minute")
@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Exchange a valid refresh token for a new access token",
)
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    cookie_token: str | None = Cookie(default=None, alias=_COOKIE_NAME),
) -> AccessTokenResponse:
    from app.core.config import settings

    if not cookie_token:
        raise UnauthorizedException("Refresh token is required")

    access_token, new_refresh_token = await AuthService(db).refresh_access_token(cookie_token)
    
    _set_refresh_cookie(
        response,
        new_refresh_token,
        is_production=settings.ENVIRONMENT == "production",
    )

    return AccessTokenResponse(access_token=access_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the current session's refresh token",
)
async def logout(
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await AuthService(db).logout(current_user.id)
    _clear_refresh_cookie(response)
    return MessageResponse(success=True, message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user's profile",
)
async def me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)
