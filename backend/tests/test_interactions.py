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

pytestmark = pytest.mark.asyncio

VALID_CUSTOMER = {
    "company_name": "Globex Corp",
    "industry": "SaaS",
    "contact_name": "Homer Simpson",
    "contact_email": "homer@globex.com",
    "contact_phone": "+14155550199",
}

VALID_INTERACTION = {
    "title": "Q1 Review Meeting",
    "interaction_type": "MEETING",
    "meeting_date": "2026-06-18T10:00:00Z",
    "notes": "Customer is happy with the onboarding process and looking to expand their team.",
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
        client, f"mgr_{uuid.uuid4().hex[:8]}@test.com"
    )


@pytest_asyncio.fixture
async def admin_tokens(client: AsyncClient, db_session: AsyncSession) -> dict:
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
    return resp.json()


@pytest_asyncio.fixture
async def viewer_tokens(client: AsyncClient, db_session: AsyncSession) -> dict:
    from app.core.security import hash_password
    from app.enums import UserRole
    from app.models.user import User

    email = f"viewer_{uuid.uuid4().hex[:8]}@test.com"
    user = User(
        first_name="Viewer",
        last_name="Test",
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


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateInteraction:
    async def test_manager_can_create_returns_201(
        self, client: AsyncClient, manager_tokens: dict, sample_customer: dict
    ) -> None:
        body = {**VALID_INTERACTION, "customer_id": sample_customer["id"]}
        resp = await client.post(
            INTERACTIONS, json=body, headers=_auth(manager_tokens)
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == VALID_INTERACTION["title"]
        assert data["interaction_type"] == "MEETING"
        assert data["customer"]["company_name"] == VALID_CUSTOMER["company_name"]
        assert data["created_by_user"] is not None

    async def test_admin_can_create_returns_201(
        self, client: AsyncClient, admin_tokens: dict, sample_customer: dict
    ) -> None:
        body = {**VALID_INTERACTION, "customer_id": sample_customer["id"]}
        resp = await client.post(
            INTERACTIONS, json=body, headers=_auth(admin_tokens)
        )
        assert resp.status_code == 201

    async def test_viewer_cannot_create_returns_403(
        self, client: AsyncClient, viewer_tokens: dict, sample_customer: dict
    ) -> None:
        body = {**VALID_INTERACTION, "customer_id": sample_customer["id"]}
        resp = await client.post(
            INTERACTIONS, json=body, headers=_auth(viewer_tokens)
        )
        assert resp.status_code == 403

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, sample_customer: dict
    ) -> None:
        body = {**VALID_INTERACTION, "customer_id": sample_customer["id"]}
        resp = await client.post(INTERACTIONS, json=body)
        assert resp.status_code == 401

    async def test_title_too_short_returns_422(
        self, client: AsyncClient, manager_tokens: dict, sample_customer: dict
    ) -> None:
        body = {
            **VALID_INTERACTION,
            "customer_id": sample_customer["id"],
            "title": "AB",
        }
        resp = await client.post(
            INTERACTIONS, json=body, headers=_auth(manager_tokens)
        )
        assert resp.status_code == 422

    async def test_notes_too_short_returns_422(
        self, client: AsyncClient, manager_tokens: dict, sample_customer: dict
    ) -> None:
        body = {
            **VALID_INTERACTION,
            "customer_id": sample_customer["id"],
            "notes": "Too short",
        }
        resp = await client.post(
            INTERACTIONS, json=body, headers=_auth(manager_tokens)
        )
        assert resp.status_code == 422

    async def test_invalid_interaction_type_returns_422(
        self, client: AsyncClient, manager_tokens: dict, sample_customer: dict
    ) -> None:
        body = {
            **VALID_INTERACTION,
            "customer_id": sample_customer["id"],
            "interaction_type": "INVALID_TYPE",
        }
        resp = await client.post(
            INTERACTIONS, json=body, headers=_auth(manager_tokens)
        )
        assert resp.status_code == 422

    async def test_nonexistent_customer_returns_404(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        body = {**VALID_INTERACTION, "customer_id": str(uuid.uuid4())}
        resp = await client.post(
            INTERACTIONS, json=body, headers=_auth(manager_tokens)
        )
        assert resp.status_code == 404

    async def test_all_interaction_types_accepted(
        self, client: AsyncClient, manager_tokens: dict, sample_customer: dict
    ) -> None:
        for itype in ("MEETING", "CALL", "EMAIL", "QBR"):
            body = {
                **VALID_INTERACTION,
                "customer_id": sample_customer["id"],
                "interaction_type": itype,
            }
            resp = await client.post(
                INTERACTIONS, json=body, headers=_auth(manager_tokens)
            )
            assert resp.status_code == 201, f"Failed for type {itype}: {resp.text}"


# ── List ──────────────────────────────────────────────────────────────────────

class TestListInteractions:
    async def test_list_returns_paginated_shape(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(INTERACTIONS, headers=_auth(manager_tokens))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "pages" in body
        assert body["page"] == 1
        assert body["total"] >= 1

    async def test_filter_by_customer_id(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_customer: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}?customer_id={sample_customer['id']}",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert all(
            item["customer_id"] == sample_customer["id"]
            for item in data["items"]
        )

    async def test_filter_by_type(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}?interaction_type=MEETING",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(
            item["interaction_type"] == "MEETING" for item in data["items"]
        )

    async def test_search_by_title(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}?search=Q1+Review",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_search_by_notes(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}?search=onboarding",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_pagination_page_size(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_customer: dict,
    ) -> None:
        for i in range(3):
            await client.post(
                INTERACTIONS,
                json={
                    **VALID_INTERACTION,
                    "customer_id": sample_customer["id"],
                    "title": f"Meeting number {i + 1} long title",
                },
                headers=_auth(manager_tokens),
            )
        resp = await client.get(
            f"{INTERACTIONS}?page_size=2&customer_id={sample_customer['id']}",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 2
        assert body["pages"] >= 2

    async def test_invalid_sort_by_returns_422(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}?sort_by=invalid_field",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 422

    async def test_viewer_can_list(
        self,
        client: AsyncClient,
        viewer_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(INTERACTIONS, headers=_auth(viewer_tokens))
        assert resp.status_code == 200


# ── Get ───────────────────────────────────────────────────────────────────────

class TestGetInteraction:
    async def test_get_by_id_includes_customer(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}/{sample_interaction['id']}",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sample_interaction["id"]
        assert "customer" in data
        assert data["customer"]["id"] == sample_interaction["customer_id"]

    async def test_viewer_can_read(
        self,
        client: AsyncClient,
        viewer_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}/{sample_interaction['id']}",
            headers=_auth(viewer_tokens),
        )
        assert resp.status_code == 200

    async def test_nonexistent_returns_404(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(
            f"{INTERACTIONS}/{uuid.uuid4()}",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 404

    async def test_unauthenticated_returns_401(
        self, client: AsyncClient, sample_interaction: dict
    ) -> None:
        resp = await client.get(f"{INTERACTIONS}/{sample_interaction['id']}")
        assert resp.status_code == 401


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdateInteraction:
    async def test_manager_can_update_title(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.put(
            f"{INTERACTIONS}/{sample_interaction['id']}",
            json={"title": "Updated Q1 Annual Review"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated Q1 Annual Review"

    async def test_admin_can_update_type(
        self,
        client: AsyncClient,
        admin_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.put(
            f"{INTERACTIONS}/{sample_interaction['id']}",
            json={"interaction_type": "QBR"},
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["interaction_type"] == "QBR"

    async def test_viewer_cannot_update_returns_403(
        self,
        client: AsyncClient,
        viewer_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.put(
            f"{INTERACTIONS}/{sample_interaction['id']}",
            json={"title": "Should Not Update Title"},
            headers=_auth(viewer_tokens),
        )
        assert resp.status_code == 403

    async def test_update_nonexistent_returns_404(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.put(
            f"{INTERACTIONS}/{uuid.uuid4()}",
            json={"title": "Title for nothing"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 404

    async def test_update_notes_too_short_returns_422(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.put(
            f"{INTERACTIONS}/{sample_interaction['id']}",
            json={"notes": "Too short"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 422

    async def test_empty_update_returns_200(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.put(
            f"{INTERACTIONS}/{sample_interaction['id']}",
            json={},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200


# ── Customer Timeline ─────────────────────────────────────────────────────────

class TestCustomerTimeline:
    async def test_timeline_returns_interactions(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_customer: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}/{sample_customer['id']}/timeline",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == sample_customer["id"]
        assert data["company_name"] == VALID_CUSTOMER["company_name"]
        assert data["total"] >= 1
        assert len(data["interactions"]) >= 1

    async def test_timeline_ordered_by_meeting_date_descending(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_customer: dict,
    ) -> None:
        dates = ["2026-01-15T10:00:00Z", "2026-06-18T10:00:00Z", "2025-12-01T09:00:00Z"]
        for date in dates:
            await client.post(
                INTERACTIONS,
                json={
                    **VALID_INTERACTION,
                    "customer_id": sample_customer["id"],
                    "meeting_date": date,
                },
                headers=_auth(manager_tokens),
            )
        resp = await client.get(
            f"{CUSTOMERS}/{sample_customer['id']}/timeline",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()
        meeting_dates = [item["meeting_date"] for item in data["interactions"]]
        assert meeting_dates == sorted(meeting_dates, reverse=True)

    async def test_viewer_can_access_timeline(
        self,
        client: AsyncClient,
        viewer_tokens: dict,
        sample_customer: dict,
        sample_interaction: dict,
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}/{sample_customer['id']}/timeline",
            headers=_auth(viewer_tokens),
        )
        assert resp.status_code == 200

    async def test_nonexistent_customer_returns_404(
        self, client: AsyncClient, manager_tokens: dict
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}/{uuid.uuid4()}/timeline",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 404

    async def test_empty_timeline_has_zero_total(
        self,
        client: AsyncClient,
        manager_tokens: dict,
        sample_customer: dict,
    ) -> None:
        resp = await client.get(
            f"{CUSTOMERS}/{sample_customer['id']}/timeline",
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["total"], int)
        assert isinstance(data["interactions"], list)
