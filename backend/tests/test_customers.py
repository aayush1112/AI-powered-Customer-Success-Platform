from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

BASE = "/api/v1"
AUTH = f"{BASE}/auth"
CUSTOMERS = f"{BASE}/customers"

pytestmark = pytest.mark.asyncio

VALID_CUSTOMER = {
    "company_name": "Acme Corp",
    "industry": "SaaS",
    "contact_name": "Jane Doe",
    "contact_email": "jane@acme.com",
    "contact_phone": "+14155550100",
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

async def _register_and_login(
    client: AsyncClient, email: str, password: str = "Password123!"
) -> dict:
    """Register a new user (MANAGER role) and return login tokens."""
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


@pytest_asyncio.fixture
async def manager_tokens(client: AsyncClient) -> dict:
    return await _register_and_login(client, f"mgr_{uuid.uuid4().hex[:8]}@test.com")


@pytest_asyncio.fixture
async def admin_tokens(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create an ADMIN user directly in the DB and return login tokens."""
    from app.core.security import hash_password
    from app.enums import UserRole
    from app.models.user import User

    email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    user = User(
        first_name="Admin",
        last_name="Test",
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
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Create ────────────────────────────────────────────────────────────────────


class TestCreateCustomer:
    async def test_manager_can_create(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.post(
            CUSTOMERS, json=VALID_CUSTOMER, headers=_auth(manager_tokens)
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["company_name"] == "Acme Corp"
        assert body["data"]["status"] == "PROSPECT"
        assert "id" in body["data"]

    async def test_admin_can_create(
        self, client: AsyncClient, admin_tokens: dict
    ) -> None:
        payload = {**VALID_CUSTOMER, "company_name": "AdminCreated Inc"}
        resp = await client.post(CUSTOMERS, json=payload, headers=_auth(admin_tokens))
        assert resp.status_code == 201

    async def test_unauthenticated_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post(CUSTOMERS, json=VALID_CUSTOMER)
        assert resp.status_code == 401

    async def test_empty_company_name_returns_422(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": ""},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 422

    async def test_invalid_email_returns_422(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "contact_email": "not-an-email"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 422

    async def test_phone_too_long_returns_422(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "contact_phone": "1" * 21},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 422

    async def test_default_status_is_prospect(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "ProspectCo"},
            headers=_auth(manager_tokens),
        )
        assert resp.json()["data"]["status"] == "PROSPECT"


# ── List ──────────────────────────────────────────────────────────────────────


class TestListCustomers:
    async def test_returns_paginated_shape(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(CUSTOMERS, headers=_auth(manager_tokens))
        assert resp.status_code == 200
        body = resp.json()
        for key in ("items", "total", "page", "page_size", "pages"):
            assert key in body

    async def test_search_filters_results(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        uid = uuid.uuid4().hex[:6]
        await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": f"UniqueXYZ_{uid}"},
            headers=_auth(manager_tokens),
        )
        resp = await client.get(
            f"{CUSTOMERS}?search=UniqueXYZ_{uid}", headers=_auth(manager_tokens)
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any(c["company_name"] == f"UniqueXYZ_{uid}" for c in items)

    async def test_status_filter_only_returns_matching(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}?status=PROSPECT", headers=_auth(manager_tokens)
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "PROSPECT"

    async def test_sort_by_company_name(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}?sort_by=company_name&sort_order=asc",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200

    async def test_invalid_sort_by_returns_422(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}?sort_by=invalid_field", headers=_auth(manager_tokens)
        )
        assert resp.status_code == 422

    async def test_pagination_params(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}?page=1&page_size=5", headers=_auth(manager_tokens)
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 5
        assert len(body["items"]) <= 5

    async def test_unauthenticated_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get(CUSTOMERS)
        assert resp.status_code == 401


# ── Get single ────────────────────────────────────────────────────────────────


class TestGetCustomer:
    async def test_returns_customer_data(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "DetailCo"},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]
        resp = await client.get(f"{CUSTOMERS}/{cid}", headers=_auth(manager_tokens))
        assert resp.status_code == 200
        assert resp.json()["company_name"] == "DetailCo"

    async def test_nonexistent_returns_404(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        zero = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"{CUSTOMERS}/{zero}", headers=_auth(manager_tokens))
        assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────


class TestUpdateCustomer:
    async def test_manager_can_update_fields(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "UpdateMe"},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]

        resp = await client.put(
            f"{CUSTOMERS}/{cid}",
            json={"status": "ACTIVE", "company_name": "Updated Inc"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "ACTIVE"
        assert data["company_name"] == "Updated Inc"

    async def test_partial_update_only_changes_sent_fields(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "PartialUpdate"},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]
        original_email = create.json()["data"]["contact_email"]

        resp = await client.put(
            f"{CUSTOMERS}/{cid}",
            json={"status": "AT_RISK"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "AT_RISK"
        assert data["contact_email"] == original_email

    async def test_update_nonexistent_returns_404(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        zero = "00000000-0000-0000-0000-000000000000"
        resp = await client.put(
            f"{CUSTOMERS}/{zero}",
            json={"status": "ACTIVE"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 404

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "AuthUpdate"},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]
        resp = await client.put(f"{CUSTOMERS}/{cid}", json={"status": "ACTIVE"})
        assert resp.status_code == 401


# ── Delete ────────────────────────────────────────────────────────────────────


class TestDeleteCustomer:
    async def test_manager_cannot_delete_returns_403(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "ManagerDelete"},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]
        resp = await client.delete(f"{CUSTOMERS}/{cid}", headers=_auth(manager_tokens))
        assert resp.status_code == 403

    async def test_admin_soft_delete_returns_204(
        self, client: AsyncClient, manager_tokens: dict, admin_tokens: dict
    ) -> None:
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "ToBeDeleted"},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]
        resp = await client.delete(f"{CUSTOMERS}/{cid}", headers=_auth(admin_tokens))
        assert resp.status_code == 204

    async def test_deleted_customer_returns_404(
        self, client: AsyncClient, manager_tokens: dict, admin_tokens: dict
    ) -> None:
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": "AlsoDeleted"},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]
        await client.delete(f"{CUSTOMERS}/{cid}", headers=_auth(admin_tokens))

        resp = await client.get(f"{CUSTOMERS}/{cid}", headers=_auth(manager_tokens))
        assert resp.status_code == 404

    async def test_deleted_customer_excluded_from_list(
        self, client: AsyncClient, manager_tokens: dict, admin_tokens: dict
    ) -> None:
        uid = uuid.uuid4().hex[:6]
        name = f"ExcludedPost_{uid}"
        create = await client.post(
            CUSTOMERS,
            json={**VALID_CUSTOMER, "company_name": name},
            headers=_auth(manager_tokens),
        )
        cid = create.json()["data"]["id"]
        await client.delete(f"{CUSTOMERS}/{cid}", headers=_auth(admin_tokens))

        resp = await client.get(
            f"{CUSTOMERS}?search={name}", headers=_auth(manager_tokens)
        )
        assert resp.status_code == 200
        assert all(c["id"] != cid for c in resp.json()["items"])

    async def test_unauthenticated_returns_401(self, client: AsyncClient) -> None:
        zero = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(f"{CUSTOMERS}/{zero}")
        assert resp.status_code == 401
