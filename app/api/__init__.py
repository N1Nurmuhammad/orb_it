"""API package: aggregates per-concern routers.

No global prefix — the spec defines bare paths (/auth/..., /me, /users).
"""

from fastapi import APIRouter

from . import auth, health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)

__all__ = ["api_router"]
