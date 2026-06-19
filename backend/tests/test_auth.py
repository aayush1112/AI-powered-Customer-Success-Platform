from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.models.user import User

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/auth"

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def register_payload() -> dict:
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "Password123!",
    }


@pytest.fixture
def login_payload() -> dict:
    return {"email": "john.doe@example.com", "password": "Password123!"}


# ── Registration ──────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient, register_payload: dict):
    res = await client.post(f"{BASE}/register", json=register_payload)
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert "registered" in body["message"].lower()


async def test_register_duplicate_email(client: AsyncClient, register_payload: dict):
    await client.post(f"{BASE}/register", json=register_payload)
    res = await client.post(f"{BASE}/register", json=register_payload)
    assert res.status_code == 409


async def test_register_weak_password(client: AsyncClient):
    res = await client.post(
        f"{BASE}/register",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "password": "weak",
        },
    )
    assert res.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    res = await client.post(
        f"{BASE}/register",
        json={
            "first_name": "A",
            "last_name": "B",
            "email": "not-an-email",
            "password": "Password123!",
        },
    )
    assert res.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(
    client: AsyncClient,
    register_payload: dict,
    login_payload: dict,
):
    await client.post(f"{BASE}/register", json=register_payload)
    res = await client.post(f"{BASE}/login", json=login_payload)

    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, register_payload: dict):
    await client.post(f"{BASE}/register", json=register_payload)
    res = await client.post(
        f"{BASE}/login",
        json={"email": register_payload["email"], "password": "WrongPass1!"},
    )
    assert res.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post(
        f"{BASE}/login",
        json={"email": "nobody@example.com", "password": "Password123!"},
    )
    assert res.status_code == 401


# ── Token refresh ─────────────────────────────────────────────────────────────

async def test_refresh_with_valid_token(
    client: AsyncClient,
    register_payload: dict,
    login_payload: dict,
):
    await client.post(f"{BASE}/register", json=register_payload)
    login_res = await client.post(f"{BASE}/login", json=login_payload)
    refresh_token = login_res.json()["refresh_token"]

    res = await client.post(
        f"{BASE}/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_refresh_with_invalid_token(client: AsyncClient):
    res = await client.post(
        f"{BASE}/refresh",
        json={"refresh_token": "this.is.not.valid"},
    )
    assert res.status_code == 401


# ── Current user ──────────────────────────────────────────────────────────────

async def test_me_returns_user_profile(
    client: AsyncClient,
    register_payload: dict,
    login_payload: dict,
):
    await client.post(f"{BASE}/register", json=register_payload)
    login_res = await client.post(f"{BASE}/login", json=login_payload)
    token = login_res.json()["access_token"]

    res = await client.get(
        f"{BASE}/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == register_payload["email"].lower()
    assert body["role"] == "MANAGER"


async def test_me_without_token_returns_401(client: AsyncClient):
    res = await client.get(f"{BASE}/me")
    assert res.status_code == 401


async def test_me_with_invalid_token_returns_401(client: AsyncClient):
    res = await client.get(
        f"{BASE}/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert res.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

async def test_logout_invalidates_refresh_token(
    client: AsyncClient,
    register_payload: dict,
    login_payload: dict,
):
    await client.post(f"{BASE}/register", json=register_payload)
    login_res = await client.post(f"{BASE}/login", json=login_payload)
    token_data = login_res.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # Logout
    await client.post(
        f"{BASE}/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Refresh should now fail
    res = await client.post(
        f"{BASE}/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res.status_code == 401


# ── RBAC ──────────────────────────────────────────────────────────────────────

async def test_new_user_has_manager_role(
    client: AsyncClient,
    register_payload: dict,
    login_payload: dict,
):
    await client.post(f"{BASE}/register", json=register_payload)
    login_res = await client.post(f"{BASE}/login", json=login_payload)
    token = login_res.json()["access_token"]

    me_res = await client.get(
        f"{BASE}/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.json()["role"] == "MANAGER"
