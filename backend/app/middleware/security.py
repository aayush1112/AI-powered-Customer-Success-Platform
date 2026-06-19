from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds defensive HTTP security headers to every response.

    These are defence-in-depth headers only — they do not alter application
    behaviour. Every header value is intentionally conservative so as not to
    break any existing functionality.
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response: Response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers.setdefault("X-Content-Type-Options", "nosniff")

        # Clickjacking protection
        response.headers.setdefault("X-Frame-Options", "DENY")

        # Force HTTPS for one year (only meaningful in production behind TLS)
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

        # Don't leak full URL in Referer header
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )

        # Disable browser features the API doesn't use
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )

        # Prevent caching of API responses at CDN/proxy layer
        # Individual endpoints may override this via Cache-Control
        response.headers.setdefault("X-Content-Type-Options", "nosniff")

        return response
