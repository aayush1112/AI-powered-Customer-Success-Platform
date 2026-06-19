"""API integration tests for /api/v1/users endpoints."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

BASE = "/api/v1"
AUTH = f"{BASE}/auth"
USERS = f"{BASE}/users"

pytestmark = pytest.mark.asyncio


# ── Fixtures ──────────────────────────────────────────────────────────────────


async def _register_and_login(
    client: AsyncClient, email: str, password: str = "Password123!"
) -> dict:
    """Register a new MANAGER user and return login tokens."""
    await client.post(
        f"{AUTH}/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )
    resp = await client.post(f"{AUTH}/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _create_admin(
    client: AsyncClient, db_session: AsyncSession
) -> tuple[dict, uuid.UUID]:
    """Create an ADMIN user directly in the DB and return tokens + user_id."""
    from app.core.security import hash_password
    from app.enums import UserRole
    from app.models.user import User

    email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    user = User(
        first_name="Admin",
        last_name="User",
        email=email,
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    user_id = user.id

    resp = await client.post(
        f"{AUTH}/login", json={"email": email, "password": "Password123!"}
    )
    assert resp.status_code == 200, resp.text
    return resp.json(), user_id


@pytest_asyncio.fixture
async def admin_tokens(client: AsyncClient, db_session: AsyncSession) -> dict:
    tokens, _ = await _create_admin(client, db_session)
    return tokens


@pytest_asyncio.fixture
async def manager_tokens(client: AsyncClient) -> dict:
    return await _register_and_login(client, f"mgr_{uuid.uuid4().hex[:8]}@test.com")


@pytest_asyncio.fixture
async def viewer_tokens(client: AsyncClient, db_session: AsyncSession) -> dict:
    from app.core.security import hash_password
    from app.enums import UserRole
    from app.models.user import User

    email = f"viewer_{uuid.uuid4().hex[:8]}@test.com"
    user = User(
        first_name="Viewer",
        last_name="User",
        email=email,
        password_hash=hash_password("Password123!"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    resp = await client.post(f"{AUTH}/login", json={"email": email, "password": "Password123!"})
    assert resp.status_code == 200
    return resp.json()


# ── GET /users — list ─────────────────────────────────────────────────────────


class TestListUsers:
    async def test_admin_can_list_users(self, client: AsyncClient, admin_tokens: dict):
        resp = await client.get(USERS, headers=_auth(admin_tokens))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "pages" in body

    async def test_manager_cannot_list_users(self, client: AsyncClient, manager_tokens: dict):
        resp = await client.get(USERS, headers=_auth(manager_tokens))
        assert resp.status_code == 403

    async def test_viewer_cannot_list_users(self, client: AsyncClient, viewer_tokens: dict):
        resp = await client.get(USERS, headers=_auth(viewer_tokens))
        assert resp.status_code == 403

    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.get(USERS)
        assert resp.status_code == 401

    async def test_pagination_defaults(self, client: AsyncClient, admin_tokens: dict):
        resp = await client.get(USERS, headers=_auth(admin_tokens))
        body = resp.json()
        assert body["page"] == 1
        assert body["page_size"] == 10

    async def test_search_param_accepted(self, client: AsyncClient, admin_tokens: dict):
        resp = await client.get(f"{USERS}?search=admin", headers=_auth(admin_tokens))
        assert resp.status_code == 200

    async def test_role_filter_accepted(self, client: AsyncClient, admin_tokens: dict):
        resp = await client.get(f"{USERS}?role=ADMIN", headers=_auth(admin_tokens))
        assert resp.status_code == 200
        for user in resp.json()["items"]:
            assert user["role"] == "ADMIN"

    async def test_invalid_sort_by_returns_422(self, client: AsyncClient, admin_tokens: dict):
        resp = await client.get(f"{USERS}?sort_by=invalid_field", headers=_auth(admin_tokens))
        assert resp.status_code == 422


# ── GET /users/{id} ───────────────────────────────────────────────────────────


class TestGetUser:
    async def test_admin_can_get_user(
        self, client: AsyncClient, admin_tokens: dict, db_session: AsyncSession
    ):
        _, uid = await _create_admin(client, db_session)
        resp = await client.get(f"{USERS}/{uid}", headers=_auth(admin_tokens))
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(uid)
        assert "email" in body
        assert "role" in body

    async def test_manager_cannot_get_user(
        self, client: AsyncClient, manager_tokens: dict, db_session: AsyncSession
    ):
        _, uid = await _create_admin(client, db_session)
        resp = await client.get(f"{USERS}/{uid}", headers=_auth(manager_tokens))
        assert resp.status_code == 403

    async def test_returns_404_for_unknown_id(self, client: AsyncClient, admin_tokens: dict):
        resp = await client.get(f"{USERS}/{uuid.uuid4()}", headers=_auth(admin_tokens))
        assert resp.status_code == 404


# ── PUT /users/{id} ───────────────────────────────────────────────────────────


class TestUpdateUser:
    async def test_admin_can_change_role(
        self, client: AsyncClient, admin_tokens: dict, db_session: AsyncSession
    ):
        from app.core.security import hash_password
        from app.enums import UserRole
        from app.models.user import User

        email = f"target_{uuid.uuid4().hex[:8]}@test.com"
        target = User(
            first_name="Target",
            last_name="User",
            email=email,
            password_hash=hash_password("Password123!"),
            role=UserRole.MANAGER,
            is_active=True,
        )
        db_session.add(target)
        await db_session.flush()

        resp = await client.put(
            f"{USERS}/{target.id}",
            json={"role": "VIEWER"},
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "VIEWER"

    async def test_admin_can_deactivate_user(
        self, client: AsyncClient, admin_tokens: dict, db_session: AsyncSession
    ):
        from app.core.security import hash_password
        from app.enums import UserRole
        from app.models.user import User

        email = f"deact_{uuid.uuid4().hex[:8]}@test.com"
        target = User(
            first_name="Deact",
            last_name="User",
            email=email,
            password_hash=hash_password("Password123!"),
            role=UserRole.MANAGER,
            is_active=True,
        )
        db_session.add(target)
        await db_session.flush()

        resp = await client.put(
            f"{USERS}/{target.id}",
            json={"is_active": False},
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_manager_cannot_update_user(
        self, client: AsyncClient, manager_tokens: dict, db_session: AsyncSession
    ):
        _, uid = await _create_admin(client, db_session)
        resp = await client.put(
            f"{USERS}/{uid}",
            json={"role": "VIEWER"},
            headers=_auth(manager_tokens),
        )
        assert resp.status_code == 403

    async def test_invalid_role_returns_422(
        self, client: AsyncClient, admin_tokens: dict, db_session: AsyncSession
    ):
        _, uid = await _create_admin(client, db_session)
        resp = await client.put(
            f"{USERS}/{uid}",
            json={"role": "SUPERUSER"},
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 422

    async def test_returns_404_for_unknown_user(
        self, client: AsyncClient, admin_tokens: dict
    ):
        resp = await client.put(
            f"{USERS}/{uuid.uuid4()}",
            json={"role": "MANAGER"},
            headers=_auth(admin_tokens),
        )
        assert resp.status_code == 404

    async def test_cannot_deactivate_last_admin(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        from app.core.security import hash_password
        from app.enums import UserRole
        from app.models.user import User

        email = f"solo_admin_{uuid.uuid4().hex[:8]}@test.com"
        solo = User(
            first_name="Solo",
            last_name="Admin",
            email=email,
            password_hash=hash_password("Password123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(solo)
        await db_session.flush()

        resp_login = await client.post(
            f"{AUTH}/login", json={"email": email, "password": "Password123!"}
        )
        solo_tokens = resp_login.json()

        resp = await client.put(
            f"{USERS}/{solo.id}",
            json={"is_active": False},
            headers=_auth(solo_tokens),
        )
        assert resp.status_code == 409
