from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

BASE = "/api/v1"
AUTH = f"{BASE}/auth"
CUSTOMERS = f"{BASE}/customers"
INTERACTIONS = f"{BASE}/interactions"
INSIGHTS = f"{BASE}/insights"

pytestmark = pytest.mark.asyncio

VALID_CUSTOMER = {
    "company_name": "Insight Corp",
    "industry": "SaaS",
    "contact_name": "Jane Doe",
    "contact_email": "jane@insightcorp.com",
    "contact_phone": "+14155550100",
}

VALID_INTERACTION = {
    "title": "Q2 Planning Session",
    "interaction_type": "MEETING",
    "meeting_date": "2026-06-18T14:00:00Z",
    "notes": (
        "We completed onboarding successfully. The customer is happy with the platform. "
        "A concern was raised about API performance. Follow-up meeting scheduled for next Tuesday."
    ),
}

MOCK_GEMINI_POSITIVE = {
    "summary": "Customer expressed satisfaction with onboarding. API performance was flagged.",
    "sentiment": "POSITIVE",
    "action_items": ["Schedule API review", "Send updated documentation"],
    "risks": ["API latency could affect renewal"],
}

MOCK_GEMINI_NEGATIVE = {
    "summary": "Customer is unhappy with delays and considering alternatives.",
    "sentiment": "NEGATIVE",
    "action_items": ["Escalate to account manager"],
    "risks": ["High churn risk", "Competitor evaluation in progress"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(
    client: AsyncClient, email: str, password: str = "Password123!"
) -> dict:
    await client.post(
        f"{AUTH}/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )
    resp = await client.post(
        f"{AUTH}/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def manager_tokens(client: AsyncClient) -> dict:
    return await _register_and_login(
        client, f"mgr_{uuid.uuid4().hex[:8]}@insight.test"
    )


@pytest_asyncio.fixture
async def admin_tokens(client: AsyncClient, db_session: AsyncSession) -> dict:
    from app.core.security import hash_password
    from app.enums import UserRole
    from app.models.user import User

    email = f"admin_{uuid.uuid4().hex[:8]}@insight.test"
    user = User(
        first_name="Admin",
        last_name="Insight",
        email=email,
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    resp = await client.post(
        f"{AUTH}/login", json={"email": email, "password": "Password123!"}
    )
    return resp.json()


@pytest_asyncio.fixture
async def viewer_tokens(client: AsyncClient, db_session: AsyncSession) -> dict:
    from app.core.security import hash_password
    from app.enums import UserRole
    from app.models.user import User

    email = f"viewer_{uuid.uuid4().hex[:8]}@insight.test"
    user = User(
        first_name="Viewer",
        last_name="Insight",
        email=email,
        password_hash=hash_password("Password123!"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    resp = await client.post(
        f"{AUTH}/login", json={"email": email, "password": "Password123!"}
    )
    return resp.json()


@pytest_asyncio.fixture
async def sample_customer(client: AsyncClient, manager_tokens: dict) -> dict:
    resp = await client.post(
        CUSTOMERS,
        json=VALID_CUSTOMER,
        headers=_auth(manager_tokens),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


@pytest_asyncio.fixture
async def sample_interaction(
    client: AsyncClient, manager_tokens: dict, sample_customer: dict
) -> dict:
    body = {**VALID_INTERACTION, "customer_id": sample_customer["id"]}
    resp = await client.post(
        INTERACTIONS,
        json=body,
        headers=_auth(manager_tokens),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


# ── Generate insight ──────────────────────────────────────────────────────────

class TestGenerateInsight:
    async def test_admin_can_generate_returns_201(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _mock(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return MOCK_GEMINI_POSITIVE

        monkeypatch.setattr(GeminiClient, "generate_json", _mock)

        resp = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["is_fallback"] is False
        data = body["data"]
        assert data["sentiment"] == "POSITIVE"
        assert data["interaction_id"] == sample_interaction["id"]
        assert len(data["action_items"]) == 2
        assert len(data["risks"]) == 1
        assert "generated_at" in data

    async def test_manager_can_generate_returns_201(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _mock(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return MOCK_GEMINI_NEGATIVE

        monkeypatch.setattr(GeminiClient, "generate_json", _mock)

        resp = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["sentiment"] == "NEGATIVE"

    async def test_viewer_cannot_generate_returns_403(
        self,
        client: AsyncClient,
        viewer_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(viewer_tokens),
        )
        assert resp.status_code == 403

    async def test_nonexistent_interaction_returns_404(
        self,
        client: AsyncClient,
        admin_tokens: dict,
    ) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"{INSIGHTS}/generate/{fake_id}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 404

    async def test_duplicate_generate_replaces_existing(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        # First generate
        async def _positive(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return MOCK_GEMINI_POSITIVE

        monkeypatch.setattr(GeminiClient, "generate_json", _positive)
        resp1 = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp1.status_code == 201
        first_id = resp1.json()["data"]["id"]

        # Second generate (negative sentiment) — should replace the first
        async def _negative(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return MOCK_GEMINI_NEGATIVE

        monkeypatch.setattr(GeminiClient, "generate_json", _negative)
        resp2 = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp2.status_code == 201
        second_data = resp2.json()["data"]
        assert second_data["sentiment"] == "NEGATIVE"
        # Same DB row (upsert), same id
        assert second_data["id"] == first_id


# ── Get insight ───────────────────────────────────────────────────────────────

class TestGetInsight:
    async def test_returns_existing_insight(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _mock(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return MOCK_GEMINI_POSITIVE

        monkeypatch.setattr(GeminiClient, "generate_json", _mock)

        # Create insight first
        await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )

        # Now GET it
        resp = await client.get(
            f"{INSIGHTS}/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["sentiment"] == "POSITIVE"
        assert data["interaction_id"] == sample_interaction["id"]

    async def test_viewer_can_read_insight(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        viewer_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _mock(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return MOCK_GEMINI_POSITIVE

        monkeypatch.setattr(GeminiClient, "generate_json", _mock)

        await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )

        resp = await client.get(
            f"{INSIGHTS}/{sample_interaction['id']}",
            headers=_auth(viewer_tokens),
        )
        assert resp.status_code == 200

    async def test_no_insight_returns_404(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        # Guaranteed-unused interaction ID that has no insight
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"{INSIGHTS}/{fake_id}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 404


# ── Regenerate insight ────────────────────────────────────────────────────────

class TestRegenerateInsight:
    async def test_admin_can_regenerate_returns_200(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _mock(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return MOCK_GEMINI_POSITIVE

        monkeypatch.setattr(GeminiClient, "generate_json", _mock)

        resp = await client.post(
            f"{INSIGHTS}/regenerate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_viewer_cannot_regenerate_returns_403(
        self,
        client: AsyncClient,
        viewer_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.post(
            f"{INSIGHTS}/regenerate/{sample_interaction['id']}",
            headers=_auth(viewer_tokens),
        )
        assert resp.status_code == 403


# ── Fallback behaviour ────────────────────────────────────────────────────────

class TestFallbackBehaviour:
    async def test_fallback_when_gemini_returns_none(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _none(self: GeminiClient, prompt: str, **kwargs: object) -> None:
            return None

        monkeypatch.setattr(GeminiClient, "generate_json", _none)

        resp = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["is_fallback"] is True
        assert body["data"]["summary"] == "AI analysis unavailable."
        assert body["data"]["sentiment"] == "NEUTRAL"
        assert body["data"]["action_items"] == []
        assert body["data"]["risks"] == []

    async def test_fallback_when_gemini_returns_invalid_schema(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _bad(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            # Missing required fields
            return {"summary": "hello"}

        monkeypatch.setattr(GeminiClient, "generate_json", _bad)

        resp = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["is_fallback"] is True
        assert body["data"]["sentiment"] == "NEUTRAL"

    async def test_fallback_when_gemini_returns_invalid_sentiment(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.ai.gemini_client import GeminiClient

        async def _bad_sentiment(self: GeminiClient, prompt: str, **kwargs: object) -> dict:
            return {
                "summary": "A valid summary here.",
                "sentiment": "GREAT",  # invalid value
                "action_items": [],
                "risks": [],
            }

        monkeypatch.setattr(GeminiClient, "generate_json", _bad_sentiment)

        resp = await client.post(
            f"{INSIGHTS}/generate/{sample_interaction['id']}",
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 201
        assert resp.json()["is_fallback"] is True


# ── Schema validation unit tests ──────────────────────────────────────────────

class TestGeminiInsightOutputSchema:
    def test_valid_positive(self) -> None:
        from app.schemas.ai_insight import GeminiInsightOutput

        out = GeminiInsightOutput.model_validate(MOCK_GEMINI_POSITIVE)
        assert out.sentiment == "POSITIVE"
        assert len(out.action_items) == 2

    def test_sentiment_normalised_to_uppercase(self) -> None:
        from app.schemas.ai_insight import GeminiInsightOutput

        out = GeminiInsightOutput.model_validate({
            **MOCK_GEMINI_POSITIVE,
            "sentiment": "positive",
        })
        assert out.sentiment == "POSITIVE"

    def test_invalid_sentiment_raises(self) -> None:
        from pydantic import ValidationError

        from app.schemas.ai_insight import GeminiInsightOutput

        with pytest.raises(ValidationError):
            GeminiInsightOutput.model_validate({**MOCK_GEMINI_POSITIVE, "sentiment": "HAPPY"})

    def test_empty_action_items_accepted(self) -> None:
        from app.schemas.ai_insight import GeminiInsightOutput

        out = GeminiInsightOutput.model_validate({
            "summary": "Short meeting.",
            "sentiment": "NEUTRAL",
            "action_items": [],
            "risks": [],
        })
        assert out.action_items == []
        assert out.risks == []

    def test_fallback_factory(self) -> None:
        from app.schemas.ai_insight import GeminiInsightOutput

        fb = GeminiInsightOutput.fallback()
        assert fb.sentiment == "NEUTRAL"
        assert fb.summary == "AI analysis unavailable."
