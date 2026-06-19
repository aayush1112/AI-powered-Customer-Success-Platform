from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.enums import UserRole

# Matches any character outside alphanumeric — treated as a "special character"
_SPECIAL = re.compile(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]')


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, examples=["John"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=8, examples=["Password123!"])

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        errors: list[str] = []
        if not re.search(r"[A-Z]", v):
            errors.append("one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("one lowercase letter")
        if not re.search(r"\d", v):
            errors.append("one digit")
        if not _SPECIAL.search(v):
            errors.append("one special character")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class RegisterResponse(BaseModel):
    success: bool = True
    message: str = "User registered successfully"


class MessageResponse(BaseModel):
    success: bool
    message: str
