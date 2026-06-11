"""Auth flow: signup -> verify -> login -> /me, plus error cases."""

from tests.conftest import get_verification_code


async def test_full_signup_verify_login_me(client):
    # 1. signup -> unverified user
    r = await client.post(
        "/auth/signup",
        json={"email": "ada@example.com", "password": "password123", "first_name": "Ada"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "ada@example.com"
    assert body["is_verified"] is False
    assert body["role"] == "user"

    # 2. verify with the code persisted on the user
    code = await get_verification_code("ada@example.com")
    assert code and len(code) == 6
    r = await client.post("/auth/verify", json={"email": "ada@example.com", "code": code})
    assert r.status_code == 200
    assert r.json()["is_verified"] is True

    # 3. login -> token pair
    r = await client.post(
        "/auth/login", json={"email": "ada@example.com", "password": "password123"}
    )
    assert r.status_code == 200
    tokens = r.json()
    assert tokens["token_type"] == "bearer"
    access, refresh = tokens["access_token"], tokens["refresh_token"]

    # 4. /me with the access token
    r = await client.get("/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ada@example.com"

    # 5. refresh -> a new access token works
    r = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    r = await client.get("/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r.status_code == 200


async def test_signup_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    assert (await client.post("/auth/signup", json=payload)).status_code == 201
    r = await client.post("/auth/signup", json=payload)
    assert r.status_code == 409


async def test_login_wrong_password(client):
    await client.post(
        "/auth/signup", json={"email": "x@example.com", "password": "password123"}
    )
    r = await client.post(
        "/auth/login", json={"email": "x@example.com", "password": "wrong-password"}
    )
    assert r.status_code == 401


async def test_verify_wrong_code(client):
    await client.post(
        "/auth/signup", json={"email": "y@example.com", "password": "password123"}
    )
    r = await client.post("/auth/verify", json={"email": "y@example.com", "code": "000000"})
    assert r.status_code == 400


async def test_login_unverified_forbidden(client):
    # An unverified account must not obtain tokens.
    await client.post(
        "/auth/signup", json={"email": "unv@example.com", "password": "password123"}
    )
    r = await client.post(
        "/auth/login", json={"email": "unv@example.com", "password": "password123"}
    )
    assert r.status_code == 403


async def test_refresh_rejects_access_token(client):
    await client.post(
        "/auth/signup", json={"email": "z@example.com", "password": "password123"}
    )
    # must verify before login is permitted
    code = await get_verification_code("z@example.com")
    await client.post("/auth/verify", json={"email": "z@example.com", "code": code})
    tokens = (
        await client.post(
            "/auth/login", json={"email": "z@example.com", "password": "password123"}
        )
    ).json()
    # passing an access token to /refresh must be rejected
    r = await client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


async def test_me_requires_auth(client):
    assert (await client.get("/me")).status_code == 401
