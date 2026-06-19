"""
Phase 8 — Redis Caching tests

Structure:
  TestCacheKeyBuilder        — key generation (pure static logic, no I/O)
  TestCacheServiceUnit       — CacheService methods with a mocked Redis client
  TestCacheDecorator         — @cache_response() decorator behaviour
  TestCacheServiceFallback   — graceful degradation when Redis is down
  TestCustomerEndpointCache  — GET /customers/{id} cache hit/miss via HTTP
  TestDashboardEndpointCache — GET /dashboard/metrics cache hit/miss via HTTP
  TestCacheInvalidation      — cache cleared on create/update/delete
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.main import app
from app.services.cache import CacheKeyBuilder, CacheService, CacheTTL, cache_response, cache_service

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _register_and_login(client: AsyncClient, *, role: str = "MANAGER") -> str:
    email = f"cache_test_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password1!",
            "first_name": "Cache",
            "last_name": "Test",
        },
    )
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "Password1!"},
    )
    return res.json()["access_token"]


# ══════════════════════════════════════════════════════════════════════════════
# TestCacheKeyBuilder
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheKeyBuilder:
    def test_customer_list_key_shape(self):
        key = CacheKeyBuilder.customer_list_key(1, 10, None, None, None, "created_at", "desc")
        assert key.startswith("customers:list:")
        assert "1:10" in key

    def test_customer_list_key_with_filters(self):
        key = CacheKeyBuilder.customer_list_key(2, 20, "acme", "ACTIVE", "SaaS", "company_name", "asc")
        assert "acme" in key
        assert "ACTIVE" in key
        assert "SaaS" in key

    def test_customer_list_key_search_none_is_empty(self):
        k1 = CacheKeyBuilder.customer_list_key(1, 10, None, None, None, "created_at", "desc")
        k2 = CacheKeyBuilder.customer_list_key(1, 10, "", None, None, "created_at", "desc")
        assert k1 == k2

    def test_customer_key(self):
        cid = uuid.uuid4()
        key = CacheKeyBuilder.customer_key(cid)
        assert key == f"customer:{cid}"

    def test_customer_timeline_key(self):
        cid = uuid.uuid4()
        assert CacheKeyBuilder.customer_timeline_key(cid) == f"customer:timeline:{cid}"

    def test_interaction_key(self):
        iid = uuid.uuid4()
        assert CacheKeyBuilder.interaction_key(iid) == f"interaction:{iid}"

    def test_insight_key(self):
        iid = uuid.uuid4()
        assert CacheKeyBuilder.insight_key(iid) == f"insight:{iid}"

    def test_dashboard_key(self):
        assert CacheKeyBuilder.dashboard_key("metrics") == "dashboard:metrics"
        assert CacheKeyBuilder.dashboard_key("customer-status") == "dashboard:customer-status"
        assert CacheKeyBuilder.dashboard_key("interaction-trends:last_30_days") == (
            "dashboard:interaction-trends:last_30_days"
        )

    def test_different_pages_produce_different_keys(self):
        k1 = CacheKeyBuilder.customer_list_key(1, 10, None, None, None, "created_at", "desc")
        k2 = CacheKeyBuilder.customer_list_key(2, 10, None, None, None, "created_at", "desc")
        assert k1 != k2


# ══════════════════════════════════════════════════════════════════════════════
# TestCacheServiceUnit
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheServiceUnit:
    """Unit tests — Redis client is replaced by AsyncMock so no real server needed."""

    def _make_svc(self) -> tuple[CacheService, MagicMock]:
        """Returns a CacheService whose internal Redis client is fully mocked."""
        svc = CacheService.__new__(CacheService)
        mock_redis = MagicMock()
        mock_redis._client = MagicMock()
        svc._redis = mock_redis
        return svc, mock_redis

    @pytest.mark.asyncio
    async def test_get_json_cache_miss_returns_none(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.get = AsyncMock(return_value=None)
        result = await svc.get_json("some:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_json_cache_hit_deserialises(self):
        svc, mock_redis = self._make_svc()
        payload = {"id": "123", "name": "Acme"}
        mock_redis._client.get = AsyncMock(return_value=json.dumps(payload))
        result = await svc.get_json("some:key")
        assert result == payload

    @pytest.mark.asyncio
    async def test_set_json_stores_serialised_value(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.set = AsyncMock(return_value=True)
        ok = await svc.set_json("some:key", {"a": 1}, ttl=300)
        assert ok is True
        call_args = mock_redis._client.set.call_args
        assert call_args[0][0] == "some:key"
        assert '"a"' in call_args[0][1]
        assert call_args[1]["ex"] == 300

    @pytest.mark.asyncio
    async def test_delete_returns_count(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.delete = AsyncMock(return_value=2)
        count = await svc.delete("k1", "k2")
        assert count == 2

    @pytest.mark.asyncio
    async def test_delete_pattern_scans_and_deletes(self):
        svc, mock_redis = self._make_svc()

        async def _scan_iter(match):
            for k in ["customers:list:1", "customers:list:2"]:
                yield k

        mock_redis._client.scan_iter = _scan_iter
        mock_redis._client.delete = AsyncMock(return_value=2)
        count = await svc.delete_pattern("customers:list:*")
        assert count == 2

    @pytest.mark.asyncio
    async def test_delete_pattern_no_matching_keys_returns_zero(self):
        svc, mock_redis = self._make_svc()

        async def _empty_scan(match):
            return
            yield  # make it an async generator

        mock_redis._client.scan_iter = _empty_scan
        count = await svc.delete_pattern("nonexistent:*")
        assert count == 0

    @pytest.mark.asyncio
    async def test_exists_true_when_key_present(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.exists = AsyncMock(return_value=1)
        assert await svc.exists("key") is True

    @pytest.mark.asyncio
    async def test_exists_false_when_key_absent(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.exists = AsyncMock(return_value=0)
        assert await svc.exists("key") is False

    @pytest.mark.asyncio
    async def test_ttl_returns_integer(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.ttl = AsyncMock(return_value=250)
        assert await svc.ttl("key") == 250

    @pytest.mark.asyncio
    async def test_increment(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.incr = AsyncMock(return_value=5)
        assert await svc.increment("counter") == 5

    @pytest.mark.asyncio
    async def test_decrement(self):
        svc, mock_redis = self._make_svc()
        mock_redis._client.decr = AsyncMock(return_value=3)
        assert await svc.decrement("counter") == 3


# ══════════════════════════════════════════════════════════════════════════════
# TestCacheDecorator
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheDecorator:
    @pytest.mark.asyncio
    async def test_miss_calls_function_and_caches_result(self):
        calls = []

        @cache_response(key_template="test:{item_id}", ttl=60)
        async def fetch_item(item_id: str) -> dict:
            calls.append(item_id)
            return {"id": item_id, "value": 42}

        with (
            patch("app.services.cache.service.cache_service") as mock_svc,
            patch("app.services.cache.decorator.cache_service", mock_svc),
        ):
            mock_svc.get_json = AsyncMock(return_value=None)
            mock_svc.set_json = AsyncMock(return_value=True)

            result = await fetch_item("abc")

        assert result == {"id": "abc", "value": 42}
        assert calls == ["abc"]
        mock_svc.set_json.assert_awaited_once()
        call_kwargs = mock_svc.set_json.call_args
        assert call_kwargs[0][0] == "test:abc"
        assert call_kwargs[1]["ttl"] == 60

    @pytest.mark.asyncio
    async def test_hit_returns_cached_without_calling_function(self):
        calls = []

        @cache_response(key_template="test:{item_id}", ttl=60)
        async def fetch_item(item_id: str) -> dict:
            calls.append(item_id)
            return {"id": item_id}

        cached_val = {"id": "xyz", "value": 99}
        with patch("app.services.cache.decorator.cache_service") as mock_svc:
            mock_svc.get_json = AsyncMock(return_value=cached_val)
            mock_svc.set_json = AsyncMock()

            result = await fetch_item("xyz")

        assert result == cached_val
        assert calls == []  # function body was NOT executed
        mock_svc.set_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unknown_template_placeholder_skips_cache(self):
        calls = []

        @cache_response(key_template="test:{nonexistent_param}", ttl=60)
        async def fetch_item(item_id: str) -> dict:
            calls.append(item_id)
            return {"id": item_id}

        # Should NOT raise — just skips caching and runs the function.
        with patch("app.services.cache.decorator.cache_service") as mock_svc:
            mock_svc.get_json = AsyncMock(return_value=None)
            mock_svc.set_json = AsyncMock()

            result = await fetch_item("abc")

        assert result == {"id": "abc"}
        assert calls == ["abc"]


# ══════════════════════════════════════════════════════════════════════════════
# TestCacheServiceFallback
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheServiceFallback:
    """Redis is unavailable — all CacheService methods must return safe defaults."""

    def _make_svc_disconnected(self) -> CacheService:
        svc = CacheService.__new__(CacheService)
        mock_redis = MagicMock()
        mock_redis._client = None  # simulate no connection
        svc._redis = mock_redis
        return svc

    @pytest.mark.asyncio
    async def test_get_json_returns_none_when_disconnected(self):
        svc = self._make_svc_disconnected()
        assert await svc.get_json("key") is None

    @pytest.mark.asyncio
    async def test_set_json_returns_false_when_disconnected(self):
        svc = self._make_svc_disconnected()
        assert await svc.set_json("key", {"a": 1}) is False

    @pytest.mark.asyncio
    async def test_delete_returns_zero_when_disconnected(self):
        svc = self._make_svc_disconnected()
        assert await svc.delete("key") == 0

    @pytest.mark.asyncio
    async def test_delete_pattern_returns_zero_when_disconnected(self):
        svc = self._make_svc_disconnected()
        assert await svc.delete_pattern("prefix:*") == 0

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_disconnected(self):
        svc = self._make_svc_disconnected()
        assert await svc.exists("key") is False

    @pytest.mark.asyncio
    async def test_exception_in_get_json_returns_none(self):
        svc, mock_redis = TestCacheServiceUnit()._make_svc()
        mock_redis._client.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        assert await svc.get_json("key") is None

    @pytest.mark.asyncio
    async def test_exception_in_set_json_returns_false(self):
        svc, mock_redis = TestCacheServiceUnit()._make_svc()
        mock_redis._client.set = AsyncMock(side_effect=ConnectionError("Redis down"))
        assert await svc.set_json("key", {"x": 1}) is False

    @pytest.mark.asyncio
    async def test_exception_in_delete_pattern_returns_zero(self):
        svc, mock_redis = TestCacheServiceUnit()._make_svc()

        async def _raise(match):
            raise ConnectionError("Redis down")
            yield  # make it an async generator

        mock_redis._client.scan_iter = _raise
        assert await svc.delete_pattern("*") == 0


# ══════════════════════════════════════════════════════════════════════════════
# HTTP-level integration tests (use real DB, mock cache_service)
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def auth_client(db_session: AsyncSession):
    """HTTP client with DB override; yields (client, auth_headers)."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        token = await _register_and_login(ac)
        yield ac, {"Authorization": f"Bearer {token}"}
    app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# TestCustomerEndpointCache
# ══════════════════════════════════════════════════════════════════════════════

class TestCustomerEndpointCache:
    @pytest.mark.asyncio
    async def test_get_customer_cache_miss_hits_db(self, auth_client):
        client, headers = auth_client

        # Create a customer first
        create_res = await client.post(
            "/api/v1/customers/",
            json={
                "company_name": "Cache Corp",
                "industry": "Tech",
                "contact_name": "Alice",
                "contact_email": "alice@cachecorp.com",
            },
            headers=headers,
        )
        assert create_res.status_code == 201
        cid = create_res.json()["data"]["id"]

        # Patch cache_service.get_json to simulate a miss, set_json to capture storage
        with (
            patch("app.api.v1.endpoints.customers.cache_service") as mock_cache,
        ):
            mock_cache.get_json = AsyncMock(return_value=None)
            mock_cache.set_json = AsyncMock(return_value=True)

            res = await client.get(f"/api/v1/customers/{cid}", headers=headers)

        assert res.status_code == 200
        assert res.json()["company_name"] == "Cache Corp"
        mock_cache.set_json.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_customer_cache_hit_skips_db(self, auth_client):
        client, headers = auth_client
        cached_payload = {
            "id": str(uuid.uuid4()),
            "company_name": "Cached Co",
            "industry": "Finance",
            "contact_name": "Bob",
            "contact_email": "bob@cached.co",
            "contact_phone": None,
            "status": "ACTIVE",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "created_by_id": str(uuid.uuid4()),
        }
        with patch("app.api.v1.endpoints.customers.cache_service") as mock_cache:
            mock_cache.get_json = AsyncMock(return_value=cached_payload)
            mock_cache.set_json = AsyncMock()

            res = await client.get(
                f"/api/v1/customers/{cached_payload['id']}", headers=headers
            )

        assert res.status_code == 200
        assert res.json()["company_name"] == "Cached Co"
        mock_cache.set_json.assert_not_awaited()  # DB was not queried

    @pytest.mark.asyncio
    async def test_create_customer_invalidates_list_and_dashboard(self, auth_client):
        client, headers = auth_client
        with patch("app.api.v1.endpoints.customers.cache_service") as mock_cache:
            mock_cache.delete_pattern = AsyncMock(return_value=0)

            res = await client.post(
                "/api/v1/customers/",
                json={
                    "company_name": "New Corp",
                    "industry": "Tech",
                    "contact_name": "Carol",
                    "contact_email": "carol@newcorp.com",
                },
                headers=headers,
            )

        assert res.status_code == 201
        # Both patterns must have been invalidated
        calls = [c.args[0] for c in mock_cache.delete_pattern.await_args_list]
        assert "customers:list:*" in calls
        assert "dashboard:*" in calls

    @pytest.mark.asyncio
    async def test_update_customer_invalidates_cache(self, auth_client):
        client, headers = auth_client
        create_res = await client.post(
            "/api/v1/customers/",
            json={
                "company_name": "Update Corp",
                "industry": "Retail",
                "contact_name": "Dave",
                "contact_email": "dave@updatecorp.com",
            },
            headers=headers,
        )
        cid = create_res.json()["data"]["id"]

        with patch("app.api.v1.endpoints.customers.cache_service") as mock_cache:
            mock_cache.delete = AsyncMock(return_value=1)
            mock_cache.delete_pattern = AsyncMock(return_value=0)

            res = await client.put(
                f"/api/v1/customers/{cid}",
                json={"company_name": "Updated Corp"},
                headers=headers,
            )

        assert res.status_code == 200
        pattern_calls = [c.args[0] for c in mock_cache.delete_pattern.await_args_list]
        assert "customers:list:*" in pattern_calls
        assert "dashboard:*" in pattern_calls


# ══════════════════════════════════════════════════════════════════════════════
# TestDashboardEndpointCache
# ══════════════════════════════════════════════════════════════════════════════

class TestDashboardEndpointCache:
    @pytest.mark.asyncio
    async def test_metrics_cache_miss_stores_result(self, auth_client):
        client, headers = auth_client
        with patch("app.api.v1.endpoints.dashboard.cache_service") as mock_cache:
            mock_cache.get_json = AsyncMock(return_value=None)
            mock_cache.set_json = AsyncMock(return_value=True)

            res = await client.get("/api/v1/dashboard/metrics", headers=headers)

        assert res.status_code == 200
        mock_cache.set_json.assert_awaited_once()
        stored_key = mock_cache.set_json.call_args[0][0]
        assert stored_key == "dashboard:metrics"

    @pytest.mark.asyncio
    async def test_metrics_cache_hit_returns_cached(self, auth_client):
        client, headers = auth_client
        cached = {
            "total_customers": 5,
            "active_customers": 3,
            "at_risk_customers": 1,
            "churned_customers": 1,
            "total_interactions": 10,
            "interactions_this_month": 2,
            "positive_insights": 4,
            "neutral_insights": 3,
            "negative_insights": 3,
        }
        with patch("app.api.v1.endpoints.dashboard.cache_service") as mock_cache:
            mock_cache.get_json = AsyncMock(return_value=cached)
            mock_cache.set_json = AsyncMock()

            res = await client.get("/api/v1/dashboard/metrics", headers=headers)

        assert res.status_code == 200
        assert res.json()["total_customers"] == 5
        mock_cache.set_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_interaction_trends_key_includes_period(self, auth_client):
        client, headers = auth_client
        with patch("app.api.v1.endpoints.dashboard.cache_service") as mock_cache:
            mock_cache.get_json = AsyncMock(return_value=None)
            mock_cache.set_json = AsyncMock(return_value=True)

            res = await client.get(
                "/api/v1/dashboard/interactions?period=last_7_days", headers=headers
            )

        assert res.status_code == 200
        stored_key = mock_cache.set_json.call_args[0][0]
        assert "last_7_days" in stored_key

    @pytest.mark.asyncio
    async def test_customer_status_cached(self, auth_client):
        client, headers = auth_client
        with patch("app.api.v1.endpoints.dashboard.cache_service") as mock_cache:
            mock_cache.get_json = AsyncMock(return_value=None)
            mock_cache.set_json = AsyncMock(return_value=True)

            res = await client.get("/api/v1/dashboard/customer-status", headers=headers)

        assert res.status_code == 200
        stored_key = mock_cache.set_json.call_args[0][0]
        assert stored_key == "dashboard:customer-status"

    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_403(self, auth_client):
        client, _ = auth_client
        res = await client.get("/api/v1/dashboard/metrics")
        assert res.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# TestCacheInvalidation
# ══════════════════════════════════════════════════════════════════════════════

class TestCacheInvalidation:
    @pytest.mark.asyncio
    async def test_interaction_create_invalidates_dashboard_and_timeline(self, auth_client):
        client, headers = auth_client

        # Need a customer first
        cust_res = await client.post(
            "/api/v1/customers/",
            json={
                "company_name": "Inv Corp",
                "industry": "Tech",
                "contact_name": "Eve",
                "contact_email": "eve@invcorp.com",
            },
            headers=headers,
        )
        cid = cust_res.json()["data"]["id"]

        with patch("app.api.v1.endpoints.interactions.cache_service") as mock_cache:
            mock_cache.delete = AsyncMock(return_value=1)
            mock_cache.delete_pattern = AsyncMock(return_value=0)

            res = await client.post(
                "/api/v1/interactions/",
                json={
                    "customer_id": cid,
                    "title": "Kickoff call",
                    "interaction_type": "CALL",
                    "meeting_date": "2025-03-01T10:00:00Z",
                },
                headers=headers,
            )

        assert res.status_code == 201
        # Timeline for this customer must have been invalidated
        delete_calls = [c.args[0] for c in mock_cache.delete.await_args_list]
        assert any("timeline" in k and cid in k for k in delete_calls)
        # Dashboard must have been invalidated
        pattern_calls = [c.args[0] for c in mock_cache.delete_pattern.await_args_list]
        assert "dashboard:*" in pattern_calls

    @pytest.mark.asyncio
    async def test_insight_generate_invalidates_insight_and_dashboard(self, auth_client):
        client, headers = auth_client

        # Create customer + interaction
        cust_res = await client.post(
            "/api/v1/customers/",
            json={
                "company_name": "Insight Corp",
                "industry": "Tech",
                "contact_name": "Frank",
                "contact_email": "frank@insightcorp.com",
            },
            headers=headers,
        )
        cid = cust_res.json()["data"]["id"]
        inter_res = await client.post(
            "/api/v1/interactions/",
            json={
                "customer_id": cid,
                "title": "Insight call",
                "interaction_type": "MEETING",
                "meeting_date": "2025-03-05T10:00:00Z",
                "notes": "Discussed roadmap.",
            },
            headers=headers,
        )
        iid = inter_res.json()["data"]["id"]

        with (
            patch("app.api.v1.endpoints.insights.cache_service") as mock_cache,
            patch("app.services.ai_insight_service.GeminiClient") as mock_gemini_cls,
        ):
            mock_cache.delete = AsyncMock(return_value=1)
            mock_cache.delete_pattern = AsyncMock(return_value=0)

            mock_gemini = mock_gemini_cls.return_value
            mock_gemini.generate_json = AsyncMock(return_value={
                "summary": "Good call.",
                "sentiment": "POSITIVE",
                "action_items": ["Follow up"],
                "risks": ["None"],
            })

            res = await client.post(
                f"/api/v1/insights/generate/{iid}", headers=headers
            )

        assert res.status_code == 201
        delete_calls = [c.args[0] for c in mock_cache.delete.await_args_list]
        assert any(iid in k for k in delete_calls)
        pattern_calls = [c.args[0] for c in mock_cache.delete_pattern.await_args_list]
        assert "dashboard:*" in pattern_calls

    @pytest.mark.asyncio
    async def test_ttl_constants(self):
        assert CacheTTL.CUSTOMER_LIST == 300
        assert CacheTTL.CUSTOMER_DETAIL == 300
        assert CacheTTL.INTERACTION_DETAIL == 300
        assert CacheTTL.AI_INSIGHT == 600
        assert CacheTTL.DASHBOARD == 300
