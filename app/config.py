"""Centralized configuration, all from environment variables.

No secrets are hardcoded here — every sensitive value (DB URL, JWT secret) is
read from the environment and provided at runtime via .env / docker-compose.
"""

import os

# --- database ---
# Async SQLAlchemy URL. In Docker this points at the "db" compose service.
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://orbit:orbit@db:5432/orbit",
)

# --- JWT / auth ---
# Secret used to sign tokens. MUST be overridden in production via JWT_SECRET.
JWT_SECRET: str = os.environ.get("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
# Access token is short-lived; refresh token is long-lived.
ACCESS_TOKEN_TTL_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_TTL_MINUTES", "15"))
REFRESH_TOKEN_TTL_DAYS: int = int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", "7"))

# --- verification ---
# 6-digit numeric code, valid for this many minutes. The sender is pluggable
# (see app/services/verification/); the console sender logs the code in dev.
VERIFICATION_CODE_TTL_MINUTES: int = int(
    os.environ.get("VERIFICATION_CODE_TTL_MINUTES", "30")
)

# Redis store for pending verification codes (OTPs). Uses a separate logical db
# from the Celery broker/backend (0/1) so OTP keys never collide with task data.
REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379/2")

# --- cleanup (Celery) ---
# Unverified users older than this many days are deleted by the periodic task.
CLEANUP_DAYS: int = int(os.environ.get("CLEANUP_DAYS", "2"))
# How often (in minutes) Celery Beat runs the cleanup task.
CLEANUP_INTERVAL_MINUTES: int = int(os.environ.get("CLEANUP_INTERVAL_MINUTES", "60"))
CELERY_BROKER_URL: str = os.environ.get(
    "CELERY_BROKER_URL", "redis://redis:6379/0"
)
CELERY_RESULT_BACKEND: str = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://redis:6379/1"
)
