from __future__ import annotations

import enum


class SentimentType(str, enum.Enum):
    """AI-assessed sentiment of a customer interaction."""

    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
