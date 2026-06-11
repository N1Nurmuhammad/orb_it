"""Repository package: the DI root (BaseRepo) plus one module per entity."""

from .base import BaseRepo, get_repo
from .user import UserRepo

__all__ = ["BaseRepo", "UserRepo", "get_repo"]
