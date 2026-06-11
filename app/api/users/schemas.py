"""Schemas for user representation and updates."""

import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ...database.models import Role


class UserRead(BaseModel):
    """Public representation of a user (never exposes the password hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Role
    is_verified: bool
    created_at: dt.datetime


class UserUpdate(BaseModel):
    """Partial update payload for PATCH /users/{id}.

    `role` is accepted here but only applied for admin callers — the router
    enforces that a regular user cannot escalate their own role.
    """

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[Role] = None
