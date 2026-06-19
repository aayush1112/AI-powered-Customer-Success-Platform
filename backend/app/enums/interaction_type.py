from __future__ import annotations

import enum


class InteractionType(str, enum.Enum):
    """Type of customer interaction recorded in the platform."""

    MEETING = "MEETING"
    CALL = "CALL"
    EMAIL = "EMAIL"
    QBR = "QBR"
