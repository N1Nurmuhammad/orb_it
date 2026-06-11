"""Authentication business logic: signup, login, refresh and verify.

This layer raises FastAPI `HTTPException`s directly. For an auth module the
error-to-status mapping is one-to-one and the indirection of a separate domain
exception layer would not earn its keep; with more time and more call sites I'd
introduce domain exceptions + handlers to keep services transport-agnostic.

Lives in the auth module (next to its router/views). Cross-cutting helpers it
builds on — password hashing/JWT and the verification sender/OTP store — stay in
app/services/ since they're reusable beyond auth.
"""

import jwt
from fastapi import HTTPException, status

from ...database.models import Role, User
from ...database.repo import BaseRepo
from ...services.security import (
    REFRESH_TOKEN,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ...services.verification import OTPStore, generate_code, get_sender
from .schemas import SignupRequest


async def signup(repo: BaseRepo, otp_store: OTPStore, data: SignupRequest) -> User:
    """Register a new, unverified user and dispatch a verification code."""
    email: str = str(data.email)
    if await repo.users.get_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    code = generate_code()
    user = User(
        email=email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=Role.user,
        is_verified=False,
    )
    await repo.users.create(user)
    await repo.commit()

    # Store the code in Redis (auto-expires via TTL) and "send" it (console in
    # dev). Done after commit so we never advertise a code for a user that
    # failed to persist.
    await otp_store.set(email, code)
    await get_sender().send_code(user.email, code)
    return user


async def login(repo: BaseRepo, email: str, password: str) -> dict:
    """Validate credentials and issue an access + refresh token pair.

    Only verified accounts may obtain tokens — an unverified user must complete
    POST /auth/verify first.
    """
    user = await repo.users.get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please verify your email first.",
        )
    return {
        "access_token": create_access_token(user.id, user.role.value),
        "refresh_token": create_refresh_token(user.id, user.role.value),
        "token_type": "bearer",
    }


async def refresh(repo: BaseRepo, refresh_token: str) -> dict:
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )
    if payload.get("type") != REFRESH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a refresh token.",
        )

    user = await repo.users.get_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    return {
        "access_token": create_access_token(user.id, user.role.value),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def verify(repo: BaseRepo, otp_store: OTPStore, email: str, code: str) -> User:
    """Confirm a user's account given a matching, unexpired code.

    The code (and its expiry) live in Redis: a missing key means either no code
    was ever issued or it has already expired via TTL.
    """
    user = await repo.users.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification for this email.",
        )
    if user.is_verified:
        return user

    stored = await otp_store.get(email)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code is missing or has expired.",
        )
    if stored != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code.",
        )

    await repo.users.update(user, {"is_verified": True})
    await repo.commit()
    await otp_store.delete(email)
    return user
