"""User management: role-based access control and updates."""

from app.database.models import Role


async def _login(client, email, password="password123"):
    r = await client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


async def test_list_users_admin_only(client, make_user):
    await make_user("user@example.com", role=Role.user)
    await make_user("admin@example.com", role=Role.admin)

    user_token = await _login(client, "user@example.com")
    admin_token = await _login(client, "admin@example.com")

    # non-admin -> 403
    assert (await client.get("/users", headers=_auth(user_token))).status_code == 403
    # admin -> 200 with both users
    r = await client.get("/users", headers=_auth(admin_token))
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_get_user_by_id_admin_only(client, make_user):
    target = await make_user("t@example.com", role=Role.user)
    await make_user("admin@example.com", role=Role.admin)

    admin_token = await _login(client, "admin@example.com")
    r = await client.get(f"/users/{target.id}", headers=_auth(admin_token))
    assert r.status_code == 200
    assert r.json()["email"] == "t@example.com"


async def test_delete_user_admin_only(client, make_user):
    target = await make_user("victim@example.com", role=Role.user)
    await make_user("admin@example.com", role=Role.admin)

    user_token = await _login(client, "victim@example.com")
    admin_token = await _login(client, "admin@example.com")

    assert (
        await client.delete(f"/users/{target.id}", headers=_auth(user_token))
    ).status_code == 403
    assert (
        await client.delete(f"/users/{target.id}", headers=_auth(admin_token))
    ).status_code == 204
    # gone now
    assert (
        await client.get(f"/users/{target.id}", headers=_auth(admin_token))
    ).status_code == 404


async def test_patch_self_allowed_role_change_forbidden(client, make_user):
    me = await make_user("self@example.com", role=Role.user)
    token = await _login(client, "self@example.com")

    # update own profile -> ok
    r = await client.patch(
        f"/users/{me.id}", headers=_auth(token), json={"first_name": "New"}
    )
    assert r.status_code == 200
    assert r.json()["first_name"] == "New"

    # try to self-promote -> 403
    r = await client.patch(
        f"/users/{me.id}", headers=_auth(token), json={"role": "admin"}
    )
    assert r.status_code == 403


async def test_patch_other_user_forbidden_for_non_admin(client, make_user):
    other = await make_user("other@example.com", role=Role.user)
    await make_user("plain@example.com", role=Role.user)
    token = await _login(client, "plain@example.com")

    r = await client.patch(
        f"/users/{other.id}", headers=_auth(token), json={"first_name": "Hax"}
    )
    assert r.status_code == 403
