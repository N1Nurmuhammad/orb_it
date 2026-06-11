"""User model and Role enum."""

import datetime as dt
import enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Role(str, enum.Enum):
    """User roles controlling access to protected endpoints."""

    user = "user"
    admin = "admin"


class User(Base):
    """An application user — credentials, profile, role and verification state."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    # Optional profile fields per the spec.
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role"), default=Role.user, nullable=False
    )

    # A freshly registered user starts unverified. The pending verification code
    # itself lives in Redis (with a TTL), not on this row — see
    # app/services/verification/store.py.
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    updated_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
