"""Unit tests for AIInsightService — Gemini and repositories are mocked."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.enums import SentimentType
from app.schemas.ai_insight import GeminiInsightOutput


_VALID_GEMINI = {
    "summary": "Customer happy with platform. Discussed renewal.",
    "sentiment": "POSITIVE",
    "action_items": ["Send renewal docs", "Schedule follow-up call"],
    "risks": ["Minor churn risk if onboarding delays continue"],
}

_NEGATIVE_GEMINI = {
    "summary": "Customer disappointed with support response times.",
    "sentiment": "NEGATIVE",
    "action_items": ["Escalate to account manager"],
    "risks": ["High churn risk", "Competitor evaluation underway"],
}


def _make_service():
    with patch("app.services.ai_insight_service.GeminiClient"):
        from app.services.ai_insight_service import AIInsightService
        svc = AIInsightService(MagicMock())

    svc._repo = MagicMock()
    svc._repo.get_by_interaction_id = AsyncMock(return_value=None)
    svc._repo.upsert = AsyncMock()

    svc._interaction_repo = MagicMock()
    svc._interaction_repo.get_with_relations = AsyncMock(return_value=None)

    svc._gemini = MagicMock()
    svc._gemini.generate_json = AsyncMock(return_value=None)

    return svc


def _make_insight(interaction_id: uuid.UUID | None = None) -> MagicMock:
    insight = MagicMock()
    insight.id = uuid.uuid4()
    insight.interaction_id = interaction_id or uuid.uuid4()
    insight.summary = _VALID_GEMINI["summary"]
    insight.sentiment = SentimentType.POSITIVE
    insight.action_items = _VALID_GEMINI["action_items"]
    insight.risks = _VALID_GEMINI["risks"]
    insight.generated_at = MagicMock()
    return insight


@pytest.fixture
def service():
    return _make_service()


@pytest.fixture
def mock_interaction():
    interaction = MagicMock()
    interaction.notes = "Long customer notes about the meeting that are at least 10 chars."
    return interaction


# ── generate ─────────────────────────────────────────────────────────────────


class TestGenerate:
    async def test_raises_404_when_interaction_not_found(self, service):
        service._interaction_repo.get_with_relations.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.generate(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_valid_gemini_response_stored_and_returned(
        self, service, mock_interaction
    ):
        interaction_id = uuid.uuid4()
        service._interaction_repo.get_with_relations.return_value = mock_interaction
        service._gemini.generate_json.return_value = _VALID_GEMINI
        service._repo.upsert.return_value = _make_insight(interaction_id)

        result = await service.generate(interaction_id)

        service._repo.upsert.assert_called_once()
        assert result.success is True
        assert result.is_fallback is False

    async def test_gemini_none_activates_fallback(self, service, mock_interaction):
        service._interaction_repo.get_with_relations.return_value = mock_interaction
        service._gemini.generate_json.return_value = None

        insight = _make_insight()
        insight.summary = "AI analysis unavailable."
        insight.sentiment = SentimentType.NEUTRAL
        insight.action_items = []
        insight.risks = []
        service._repo.upsert.return_value = insight

        result = await service.generate(uuid.uuid4())

        assert result.is_fallback is True

    async def test_gemini_missing_fields_activates_fallback(
        self, service, mock_interaction
    ):
        service._interaction_repo.get_with_relations.return_value = mock_interaction
        # Only 'summary' — missing sentiment/action_items/risks
        service._gemini.generate_json.return_value = {"summary": "Only summary"}

        insight = _make_insight()
        insight.summary = "AI analysis unavailable."
        insight.sentiment = SentimentType.NEUTRAL
        insight.action_items = []
        insight.risks = []
        service._repo.upsert.return_value = insight

        result = await service.generate(uuid.uuid4())
        assert result.is_fallback is True

    async def test_gemini_invalid_sentiment_activates_fallback(
        self, service, mock_interaction
    ):
        service._interaction_repo.get_with_relations.return_value = mock_interaction
        service._gemini.generate_json.return_value = {
            **_VALID_GEMINI,
            "sentiment": "AMAZING",  # not in SentimentType enum
        }
        insight = _make_insight()
        insight.sentiment = SentimentType.NEUTRAL
        service._repo.upsert.return_value = insight

        result = await service.generate(uuid.uuid4())
        assert result.is_fallback is True

    async def test_upsert_called_with_correct_args(self, service, mock_interaction):
        iid = uuid.uuid4()
        service._interaction_repo.get_with_relations.return_value = mock_interaction
        service._gemini.generate_json.return_value = _VALID_GEMINI
        service._repo.upsert.return_value = _make_insight(iid)

        await service.generate(iid)

        kw = service._repo.upsert.call_args.kwargs
        assert kw["interaction_id"] == iid
        assert kw["summary"] == _VALID_GEMINI["summary"]
        assert kw["sentiment"] == SentimentType.POSITIVE
        assert kw["action_items"] == _VALID_GEMINI["action_items"]
        assert kw["risks"] == _VALID_GEMINI["risks"]


# ── get_by_interaction ────────────────────────────────────────────────────────


class TestGetByInteraction:
    async def test_raises_404_when_no_insight(self, service):
        service._repo.get_by_interaction_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.get_by_interaction(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_returns_stored_insight(self, service):
        insight = _make_insight()
        service._repo.get_by_interaction_id.return_value = insight
        result = await service.get_by_interaction(uuid.uuid4())
        assert result is insight


# ── _parse_gemini_output ──────────────────────────────────────────────────────


class TestParseGeminiOutput:
    def test_none_returns_fallback(self, service):
        output, is_fallback = service._parse_gemini_output(None, uuid.uuid4())
        assert is_fallback is True
        assert output.sentiment == "NEUTRAL"
        assert output.summary == "AI analysis unavailable."
        assert output.action_items == []
        assert output.risks == []

    def test_valid_dict_returns_no_fallback(self, service):
        output, is_fallback = service._parse_gemini_output(_VALID_GEMINI, uuid.uuid4())
        assert is_fallback is False
        assert output.sentiment == "POSITIVE"
        assert len(output.action_items) == 2

    def test_bad_schema_returns_fallback(self, service):
        bad = {"only_key": "value"}
        output, is_fallback = service._parse_gemini_output(bad, uuid.uuid4())
        assert is_fallback is True

    def test_sentiment_normalised_uppercase(self, service):
        data = {**_VALID_GEMINI, "sentiment": "positive"}
        output, is_fallback = service._parse_gemini_output(data, uuid.uuid4())
        assert is_fallback is False
        assert output.sentiment == "POSITIVE"

    def test_negative_sentiment_parsed(self, service):
        output, is_fallback = service._parse_gemini_output(_NEGATIVE_GEMINI, uuid.uuid4())
        assert is_fallback is False
        assert output.sentiment == "NEGATIVE"


# ── GeminiInsightOutput schema ────────────────────────────────────────────────


class TestGeminiInsightOutputSchema:
    def test_fallback_factory(self):
        fb = GeminiInsightOutput.fallback()
        assert fb.sentiment == "NEUTRAL"
        assert fb.summary == "AI analysis unavailable."
        assert fb.action_items == []
        assert fb.risks == []

    def test_valid_model_validates(self):
        out = GeminiInsightOutput.model_validate(_VALID_GEMINI)
        assert out.sentiment == "POSITIVE"

    def test_invalid_sentiment_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GeminiInsightOutput.model_validate({**_VALID_GEMINI, "sentiment": "HAPPY"})
