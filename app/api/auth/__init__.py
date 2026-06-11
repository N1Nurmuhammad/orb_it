"""Auth module: authentication endpoints and shared auth dependencies."""

from .deps import get_current_user, require_admin
from .router import router
from . import views  # noqa: F401 — importing registers the endpoints onto `router`

__all__ = ["get_current_user", "require_admin", "router"]
