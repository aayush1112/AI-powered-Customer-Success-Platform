from __future__ import annotations

import time

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("Password123!")
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_password_correct():
    hashed = hash_password("Password123!")
    assert verify_password("Password123!", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("Password123!")
    assert verify_password("WrongPassword!", hashed) is False


def test_hash_is_different_each_call():
    h1 = hash_password("Password123!")
    h2 = hash_password("Password123!")
    assert h1 != h2  # bcrypt uses random salt


# ── Access token ──────────────────────────────────────────────────────────────

def test_create_access_token_contains_expected_claims():
    token = create_access_token({"sub": "user-123", "email": "a@b.com", "role": "MANAGER"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == "user-123"
    assert payload["email"] == "a@b.com"
    assert payload["role"] == "MANAGER"
    assert payload["type"] == ACCESS_TOKEN_TYPE
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_expires_in_15_minutes():
    token = create_access_token({"sub": "x"})
    payload = decode_token(token)
    delta = payload["exp"] - payload["iat"]
    assert delta == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


# ── Refresh token ─────────────────────────────────────────────────────────────

def test_create_refresh_token_has_correct_type():
    token = create_refresh_token({"sub": "user-456"})
    payload = decode_token(token)
    assert payload["type"] == REFRESH_TOKEN_TYPE


def test_refresh_token_expires_in_7_days():
    token = create_refresh_token({"sub": "x"})
    payload = decode_token(token)
    delta = payload["exp"] - payload["iat"]
    assert delta == settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


# ── decode_token ──────────────────────────────────────────────────────────────

def test_decode_token_valid():
    token = create_access_token({"sub": "abc"})
    payload = decode_token(token)
    assert payload["sub"] == "abc"


def test_decode_token_tampered_raises():
    from jose import JWTError

    token = create_access_token({"sub": "abc"})
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(JWTError):
        decode_token(tampered)


def test_decode_token_wrong_key_raises():
    from jose import JWTError, jwt as jose_jwt

    token = jose_jwt.encode({"sub": "x"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(JWTError):
        decode_token(token)
