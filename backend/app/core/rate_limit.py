from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global default limit is 100 requests per minute per IP.
# This applies to all routes unless they are decorated with `@limiter.exempt` or have a specific limit.
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
