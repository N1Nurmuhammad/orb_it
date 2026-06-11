"""User management endpoints, registered on the users router.

Handlers live here and attach to the router defined in router.py via the
`@users_router.*` decorators. Importing this module is what wires the routes.
"""

from fastapi import Depends, HTTPException, Query, status

from ...database.models import Role, User
from ...database.repo import BaseRepo, get_repo
from ..auth.deps import get_current_user, require_admin
from .router import router as users_router
from .schemas import UserRead, UserUpdate


@users_router.get(
    "/me",
    response_model=UserRead,
    summary="Get the current user",
    description="Return the profile of the authenticated user.",
)
async def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@users_router.get(
    "/users",
    response_model=list[UserRead],
    summary="List users (admin only)",
    description="Return a paginated list of all users. Requires admin role.",
)
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    repo: BaseRepo = Depends(get_repo),
) -> list[UserRead]:
    users = await repo.users.list(limit=limit, offset=offset)
    return [UserRead.model_validate(u) for u in users]


@users_router.get(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Get a user by ID (admin only)",
    description="Return a single user by ID. Requires admin role.",
)
async def get_user(
    user_id: int,
    _: User = Depends(require_admin),
    repo: BaseRepo = Depends(get_repo),
) -> UserRead:
    user = await repo.users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserRead.model_validate(user)


@users_router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Update a user (partial)",
    description=(
        "Partially update a user. A user may update their own profile; admins "
        "may update anyone. Only admins may change a user's role."
    ),
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    repo: BaseRepo = Depends(get_repo),
) -> UserRead:
    is_admin = current_user.role == Role.admin
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own account.",
        )

    user = await repo.users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    data = payload.model_dump(exclude_unset=True)
    # Only admins may change roles; reject a non-admin's role attempt.
    if "role" in data and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins may change a user's role.",
        )

    await repo.users.update(user, data)
    await repo.commit()
    return UserRead.model_validate(user)


@users_router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (admin only)",
    description="Permanently delete a user by ID. Requires admin role.",
)
async def delete_user(
    user_id: int,
    _: User = Depends(require_admin),
    repo: BaseRepo = Depends(get_repo),
) -> None:
    user = await repo.users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    await repo.users.delete(user)
    await repo.commit()
