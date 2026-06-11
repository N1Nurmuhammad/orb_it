"""Test fixtures.

Tests run against an in-memory SQLite database (aiosqlite + StaticPool so every
session shares one connection) — no Postgres/Redis needed. The app's `get_repo`
dependency is overridden to bind to this test database.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.models import Base, Role, User
from app.database.repo import BaseRepo, get_repo
from app.main import app
from app.services.security import hash_password
from app.services.verification import get_otp_store

test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def _override_get_repo():
    async with TestSession() as session:
        yield BaseRepo(session)


class FakeOTPStore:
    """In-memory OTP store standing in for Redis in tests.

    Same async interface as app.services.verification.store.OTPStore. TTL/expiry
    is Redis' responsibility and isn't exercised here (it's wall-clock based);
    these tests cover the issue / match / mismatch / delete behaviour.
    """

    def __init__(self) -> None:
        self._codes: dict[str, str] = {}

    async def set(self, email: str, code: str) -> None:
        self._codes[email] = code

    async def get(self, email: str) -> str | None:
        return self._codes.get(email)

    async def delete(self, email: str) -> None:
        self._codes.pop(email, None)


# Single shared fake store so signup and verify see the same codes within a test.
fake_otp_store = FakeOTPStore()


async def _override_get_otp_store():
    return fake_otp_store


app.dependency_overrides[get_repo] = _override_get_repo
app.dependency_overrides[get_otp_store] = _override_get_otp_store


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    fake_otp_store._codes.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def make_user():
    """Factory creating a user directly in the DB (bypassing signup)."""

    async def _make(
        email: str,
        password: str = "password123",
        role: Role = Role.user,
        is_verified: bool = True,
    ) -> User:
        async with TestSession() as session:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                role=role,
                is_verified=is_verified,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    return _make


async def get_verification_code(email: str) -> str | None:
    """Read a user's current verification code from the (fake) OTP store."""
    return await fake_otp_store.get(email)
