from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """User role controlling platform access level."""

    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    VIEWER = "VIEWER"
