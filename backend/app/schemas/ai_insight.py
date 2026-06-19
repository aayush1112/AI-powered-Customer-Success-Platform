from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import SentimentType

_VALID_SENTIMENTS = frozenset({"POSITIVE", "NEUTRAL", "NEGATIVE"})

_FALLBACK_SUMMARY = "AI analysis unavailable."


# ── Internal: validates raw Gemini JSON output ────────────────────────────────

class GeminiInsightOutput(BaseModel):
    """Strict validation of the JSON returned by Gemini.

    Normalises sentiment to uppercase and rejects any value outside the
    POSITIVE / NEUTRAL / NEGATIVE enum so the rest of the system never sees
    an invalid value.
    """

    summary: str = Field(..., min_length=1, max_length=5000)
    sentiment: str
    action_items: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalise_sentiment(cls, v: object) -> str:
        normalised = str(v).upper().strip()
        if normalised not in _VALID_SENTIMENTS:
            raise ValueError(
                f"Invalid sentiment '{v}'. Must be one of: {', '.join(sorted(_VALID_SENTIMENTS))}"
            )
        return normalised

    @field_validator("action_items", "risks", mode="before")
    @classmethod
    def coerce_string_list(cls, v: object) -> list[str]:
        if not isinstance(v, list):
            return []
        return [str(item) for item in v if item]

    @classmethod
    def fallback(cls) -> "GeminiInsightOutput":
        return cls(
            summary=_FALLBACK_SUMMARY,
            sentiment="NEUTRAL",
            action_items=[],
            risks=[],
        )


# ── API response schemas ──────────────────────────────────────────────────────

class AIInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    interaction_id: uuid.UUID
    summary: str
    sentiment: SentimentType
    action_items: list[str]
    risks: list[str]
    generated_at: datetime


class AIInsightGenerateResponse(BaseModel):
    success: bool = True
    data: AIInsightResponse
    is_fallback: bool = False
