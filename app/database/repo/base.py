"""Repository foundation: the session-carrying base, the DI root and the
FastAPI dependency.

Per-entity repositories live in sibling modules (e.g. `user.py`) and are exposed
as cached properties on `BaseRepo`:

    repo.users.get_by_email(...)

Add a new model by writing a `<Model>Repo` in its own module and adding a
cached_property here.
"""

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import SessionLocal

if TYPE_CHECKING:
    from .user import UserRepo


@dataclass
class _SessionRepo:
    """Base for every sub-repository: just carries the session."""

    session: AsyncSession


@dataclass
class BaseRepo:
    """DI root. Holds the session; sub-repos hang off it as properties."""

    session: AsyncSession

    async def commit(self) -> None:
        await self.session.commit()

    @cached_property
    def users(self) -> "UserRepo":
        # Local import keeps base.py free of a base<->user import cycle.
        from .user import UserRepo

        return UserRepo(self.session)


async def get_repo():
    """FastAPI dependency yielding a BaseRepo bound to a fresh session."""
    async with SessionLocal() as session:
        yield BaseRepo(session)
