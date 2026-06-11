"""Periodic Celery tasks.

The app's data layer is async (asyncpg) while Celery tasks are sync, so each task
drives the async repository via `asyncio.run`. Because `asyncio.run` opens a fresh
event loop per call, the task uses its OWN engine with a NullPool — no pooled
connection survives between runs. Reusing the app's shared engine would hand the
new loop a connection bound to a previous, now-closed loop and raise "attached to
a different loop". For a high-throughput worker you'd use a dedicated sync engine
(psycopg) instead; here this keeps a single async repository as the source of truth.
"""

import asyncio
import datetime as dt

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from ..config import CLEANUP_DAYS, DATABASE_URL
from ..database.repo import BaseRepo
from .celery_app import celery


async def _cleanup_unverified() -> int:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=CLEANUP_DAYS)
    # Per-run engine (NullPool) created and disposed inside this event loop, so
    # nothing is shared across Beat ticks / event loops.
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            repo = BaseRepo(session)
            deleted = await repo.users.delete_unverified_older_than(cutoff)
            await repo.commit()
            return deleted
    finally:
        await engine.dispose()


@celery.task(name="app.workers.tasks.cleanup_unverified_users")
def cleanup_unverified_users() -> int:
    """Delete users still unverified after CLEANUP_DAYS. Returns count removed."""
    deleted = asyncio.run(_cleanup_unverified())
    print(f"[CLEANUP] removed {deleted} unverified user(s)", flush=True)
    return deleted
