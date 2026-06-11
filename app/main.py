"""
ORB IT — Users API — application entrypoint.

Thin assembly layer: wires the API router. The DB schema is managed by Alembic
migrations (run on container start via entrypoint.sh), not by the app at
runtime. The actual logic lives in:
  - app/api/<feature>/ -> per-feature vertical slice: router, views, service,
                          schemas (and deps for auth) — see app/api/auth, app/api/users
  - app/services/      -> cross-cutting helpers: security (JWT/bcrypt) and the
                          verification sender + Redis OTP store
  - app/database/      -> models, repositories, engine/session config
  - app/workers/       -> Celery cleanup of unverified users
  - app/config.py      -> environment-driven configuration

A modular monolith: each feature is its own module, wired together here.
"""

from fastapi import FastAPI

from .api import api_router

app = FastAPI(
    title="ORB IT — Users API",
    description=(
        "User management: registration, JWT authentication, email verification, "
        "role-based access control, and user administration."
    ),
    version="1.0.0",
)
app.include_router(api_router)
