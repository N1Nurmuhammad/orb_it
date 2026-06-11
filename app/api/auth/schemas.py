"""Schemas for the authentication endpoints."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Registration payload. First/last name are optional per the spec."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    """Credentials exchanged for a token pair."""

    email: EmailStr
    password: str


class TokenPair(BaseModel):
    """Issued access + refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """A refresh token exchanged for a fresh access token."""

    refresh_token: str


class VerifyRequest(BaseModel):
    """Email + verification code submitted to confirm an account."""

    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
