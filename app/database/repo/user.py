"""Data access for the `users` table."""

import datetime as dt
from typing import Optional

from sqlalchemy import delete, select

from ..models import User
from .base import _SessionRepo


class UserRepo(_SessionRepo):
    """Data access for the `users` table."""

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        rows = await self.session.execute(select(User).where(User.email == email))
        return rows.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Add a User instance to the session (caller commits)."""
        self.session.add(user)
        await self.session.flush()
        return user

    async def list(self, limit: int = 50, offset: int = 0) -> list[User]:
        """Users ordered by id; paginated via limit/offset."""
        rows = await self.session.execute(
            select(User).order_by(User.id).limit(limit).offset(offset)
        )
        return list(rows.scalars().all())

    async def update(self, user: User, data: dict) -> User:
        """Apply a partial update to a User and flush."""
        for field, value in data.items():
            setattr(user, field, value)
        await self.session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)

    async def delete_unverified_older_than(self, cutoff: dt.datetime) -> int:
        """Bulk-delete unverified users created before `cutoff`. Returns count."""
        result = await self.session.execute(
            delete(User).where(
                User.is_verified.is_(False), User.created_at < cutoff
            )
        )
        return result.rowcount or 0
