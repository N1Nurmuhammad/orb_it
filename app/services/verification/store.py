"""Redis-backed store for pending verification codes (OTPs).

Codes are ephemeral, so they live in Redis rather than the relational store: a
key TTL gives us automatic expiry (no expiry column, no manual time comparison),
and the code never lingers in Postgres. Redis is already a dependency (Celery
broker/backend); OTPs use a separate logical db (REDIS_URL, default db 2).
"""

from redis.asyncio import Redis

from ...config import REDIS_URL, VERIFICATION_CODE_TTL_MINUTES

# One shared async client / connection pool for the process.
_redis: Redis = Redis.from_url(REDIS_URL, decode_responses=True)

_KEY_PREFIX = "otp:verify:"
_TTL_SECONDS = VERIFICATION_CODE_TTL_MINUTES * 60


class OTPStore:
    """Thin async wrapper over Redis for verification codes, keyed by email."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    @staticmethod
    def _key(email: str) -> str:
        return f"{_KEY_PREFIX}{email}"

    async def set(self, email: str, code: str) -> None:
        """Store `code` for `email` with the configured TTL (auto-expires)."""
        await self._client.set(self._key(email), code, ex=_TTL_SECONDS)

    async def get(self, email: str) -> str | None:
        """Return the pending code for `email`, or None if absent/expired."""
        return await self._client.get(self._key(email))

    async def delete(self, email: str) -> None:
        """Remove the pending code for `email` (called after a successful verify)."""
        await self._client.delete(self._key(email))


async def get_otp_store() -> OTPStore:
    """FastAPI dependency yielding the Redis-backed OTP store."""
    return OTPStore(_redis)
