"""Auth dependencies: current-user resolution and the admin guard.

Lives in the auth module; other modules (e.g. users) import these guards from
here via `from ..auth.deps import get_current_user, require_admin`.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ...database.models import Role, User
from ...database.repo import BaseRepo, get_repo
from ...services.security import ACCESS_TOKEN, decode_token

# tokenUrl is informational (the login endpoint); it powers Swagger's "Authorize".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    repo: BaseRepo = Depends(get_repo),
) -> User:
    """Decode the bearer access token and load the corresponding user."""
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise _credentials_error

    if payload.get("type") != ACCESS_TOKEN:
        raise _credentials_error

    user = await repo.users.get_by_id(int(payload["sub"]))
    if user is None:
        raise _credentials_error
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allow only admin users; raise 403 otherwise."""
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user
