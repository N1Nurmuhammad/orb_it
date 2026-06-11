"""Models package: the declarative Base plus one module per entity.

Importing this package registers every model on `Base.metadata` (Alembic and
`create_all` rely on that), so add a new entity by creating `<entity>.py` and
re-exporting its classes here.
"""

from .base import Base
from .user import Role, User

__all__ = ["Base", "Role", "User"]
