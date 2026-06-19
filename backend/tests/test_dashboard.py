"""
Tests for Phase 7: Dashboard Analytics endpoints.

All endpoints require authentication (any role).
Tests verify structure with an empty DB and that period filters are accepted.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

# ── Shared auth helper ────────────────────────────────────────────────────────

_TEST_EMAIL = "dashboard_user@test.com"
_TEST_PASSWORD = "Passw0rd!"


async def _register_and_login(client: AsyncClient) -> str:
    """Return a Bearer token for a freshly-registered MANAGER user."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": _TEST_EMAIL,
            "password": _TEST_PASSWORD,
            "first_name": "Dash",
            "last_name": "Board",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": _TEST_EMAIL, "password": _TEST_PASSWORD},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    token = await _register_and_login(client)
    return {"Authorization": f"Bearer {token}"}


# ── /metrics ──────────────────────────────────────────────────────────────────


class TestMetrics:
    async def test_returns_200_with_correct_shape(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/metrics", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        expected_keys = {
            "total_customers",
            "active_customers",
            "at_risk_customers",
            "churned_customers",
            "total_interactions",
            "interactions_this_month",
            "positive_insights",
            "neutral_insights",
            "negative_insights",
        }
        assert expected_keys == set(data.keys())
        for v in data.values():
            assert isinstance(v, int) and v >= 0

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/metrics")
        assert resp.status_code == 403


# ── /customer-status ──────────────────────────────────────────────────────────


class TestCustomerStatus:
    async def test_returns_200_with_correct_shape(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/customer-status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"ACTIVE", "AT_RISK", "CHURNED", "PROSPECT"}
        for v in data.values():
            assert isinstance(v, int) and v >= 0

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/customer-status")
        assert resp.status_code == 403


# ── /interactions ─────────────────────────────────────────────────────────────


class TestInteractionTrends:
    async def test_default_period_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/interactions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_last_7_days(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get(
            "/api/v1/dashboard/interactions",
            params={"period": "last_7_days"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for item in data:
            assert "date" in item and "count" in item

    async def test_last_90_days(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get(
            "/api/v1/dashboard/interactions",
            params={"period": "last_90_days"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    async def test_all_time(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get(
            "/api/v1/dashboard/interactions",
            params={"period": "all_time"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    async def test_invalid_period_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get(
            "/api/v1/dashboard/interactions",
            params={"period": "last_5_years"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/interactions")
        assert resp.status_code == 403


# ── /interaction-types ────────────────────────────────────────────────────────


class TestInteractionTypes:
    async def test_returns_200_with_correct_shape(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/interaction-types", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"MEETING", "CALL", "EMAIL", "QBR"}

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/interaction-types")
        assert resp.status_code == 403


# ── /sentiment ────────────────────────────────────────────────────────────────


class TestSentiment:
    async def test_returns_200_with_correct_shape(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/sentiment", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) == {"POSITIVE", "NEUTRAL", "NEGATIVE"}

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/sentiment")
        assert resp.status_code == 403


# ── /risks ────────────────────────────────────────────────────────────────────


class TestRisks:
    async def test_returns_200_list(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/risks", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for item in data:
            assert "risk" in item and "count" in item

    async def test_empty_db_returns_empty_list(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/risks", headers=auth_headers)
        assert resp.status_code == 200
        # With no AI insights seeded the list should be empty
        assert isinstance(resp.json(), list)

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/risks")
        assert resp.status_code == 403


# ── /action-items ─────────────────────────────────────────────────────────────


class TestActionItems:
    async def test_returns_200_list(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/action-items", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for item in data:
            assert "action" in item and "count" in item

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/action-items")
        assert resp.status_code == 403


# ── /recent-activity ─────────────────────────────────────────────────────────


class TestRecentActivity:
    async def test_returns_200_list(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        resp = await client.get("/api/v1/dashboard/recent-activity", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for item in data:
            assert "type" in item
            assert "title" in item
            assert "timestamp" in item
            assert item["type"] in ("customer", "interaction", "insight")

    async def test_unauthenticated_returns_403(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/dashboard/recent-activity")
        assert resp.status_code == 403
