"""Users module: user management endpoints."""

from .router import router
from . import views  # noqa: F401 — importing registers the endpoints onto `router`

__all__ = ["router"]
