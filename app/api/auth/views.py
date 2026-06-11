"""Authentication endpoints, registered on the auth router.

Handlers live here and attach themselves to the router defined in router.py via
the `@auth_router.*` decorators. Importing this module is what wires the routes.
"""

from fastapi import Depends, status

from ...database.repo import BaseRepo, get_repo
from ...services.verification import OTPStore, get_otp_store
from ..users.schemas import UserRead
from . import service as auth_service
from .router import router as auth_router
from .schemas import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenPair,
    VerifyRequest,
)


@auth_router.post(
    "/signup",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new account with email and password (optional first/last "
        "name). Email must be unique. The user starts unverified and a 6-digit "
        "verification code is dispatched (printed to the console in dev)."
    ),
)
async def signup(
    payload: SignupRequest,
    repo: BaseRepo = Depends(get_repo),
    otp_store: OTPStore = Depends(get_otp_store),
) -> UserRead:
    user = await auth_service.signup(repo, otp_store, payload)
    return UserRead.model_validate(user)


@auth_router.post(
    "/login",
    response_model=TokenPair,
    summary="Log in and obtain tokens",
    description=(
        "Validate credentials and return a JWT access + refresh token pair. "
        "The account must be verified — returns 403 otherwise."
    ),
)
async def login(
    payload: LoginRequest, repo: BaseRepo = Depends(get_repo)
) -> TokenPair:
    tokens = await auth_service.login(repo, str(payload.email), payload.password)
    return TokenPair(**tokens)


@auth_router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh the access token",
    description="Exchange a valid refresh token for a new access token.",
)
async def refresh(
    payload: RefreshRequest, repo: BaseRepo = Depends(get_repo)
) -> TokenPair:
    tokens = await auth_service.refresh(repo, payload.refresh_token)
    return TokenPair(**tokens)


@auth_router.post(
    "/verify",
    response_model=UserRead,
    summary="Verify an account",
    description=(
        "Confirm an account by submitting the email and the 6-digit code. On "
        "success the user becomes verified and the code is cleared."
    ),
)
async def verify(
    payload: VerifyRequest,
    repo: BaseRepo = Depends(get_repo),
    otp_store: OTPStore = Depends(get_otp_store),
) -> UserRead:
    user = await auth_service.verify(repo, otp_store, str(payload.email), payload.code)
    return UserRead.model_validate(user)
