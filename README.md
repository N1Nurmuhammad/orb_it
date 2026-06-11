# ORB IT — Users API

A production-ready, extensible **modular monolith** implementing the user-management
block: registration, JWT authentication, email verification, role-based access control,
user administration, and automatic cleanup of unverified accounts.

Built with **FastAPI** (async), **SQLAlchemy 2.0** (async, asyncpg), **PostgreSQL**,
**Alembic**, and **Celery + Redis**.

---

## Quick start (Docker)

```bash
cp .env.example .env          # adjust JWT_SECRET etc.
docker compose up --build
```

This starts five services: `api` (FastAPI on **:8000**), `db` (PostgreSQL),
`redis`, `celery-worker`, and `celery-beat`. Migrations run automatically on
container start (`entrypoint.sh` → `alembic upgrade head`).

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health: <http://localhost:8000/health>

### Try the flow

```bash
# 1. Register (returns the new, unverified user)
curl -sX POST localhost:8000/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"a@example.com","password":"password123","first_name":"Ada"}'

# 2. Grab the 6-digit code from the api logs:
docker compose logs api | grep VERIFICATION

# 3. Verify
curl -sX POST localhost:8000/auth/verify \
  -H 'Content-Type: application/json' \
  -d '{"email":"a@example.com","code":"<CODE>"}'

# 4. Log in -> tokens
curl -sX POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"a@example.com","password":"password123"}'

# 5. Call /me with the access token
curl -s localhost:8000/me -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Local development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point at a local DB (Postgres, or SQLite for a quick spin):
export DATABASE_URL="postgresql+asyncpg://orbit:orbit@localhost:5432/orbit"
alembic upgrade head
uvicorn app.main:app --reload

# Celery (separate terminals, needs a running Redis):
celery -A app.workers.celery_app.celery worker -l info
celery -A app.workers.celery_app.celery beat -l info
```

Run the tests (no external services required — they use SQLite/aiosqlite):

```bash
pytest
```

---

## Architecture

A modular monolith: each concern is an isolated module, assembled in `app/main.py`.

```
app/
├── main.py            # FastAPI app; includes the API router
├── config.py          # all configuration from environment variables
├── api/               # HTTP layer, split into feature modules
│   ├── __init__.py    #   aggregates routers (no global prefix)
│   ├── health.py      #   GET /health
│   ├── auth/          #   auth module
│   │   ├── router.py  #     the APIRouter instance (prefix/tags)
│   │   ├── views.py   #     POST /auth/{signup,login,refresh,verify} handlers
│   │   ├── service.py #     signup / login / refresh / verify business logic
│   │   ├── schemas.py #     Signup/Login/Verify/Refresh requests, TokenPair
│   │   └── deps.py    #     get_current_user, require_admin (role guard)
│   └── users/         #   users module
│       ├── router.py  #     the APIRouter instance
│       ├── views.py   #     GET /me, /users, /users/{id}; PATCH/DELETE /users/{id}
│       └── schemas.py #     UserRead, UserUpdate
├── services/          # cross-cutting helpers (reused beyond one module)
│   ├── security.py    #   bcrypt hashing + JWT (access/refresh) encode/decode
│   └── verification/  #   pluggable code sender + Redis OTP store
├── database/          # persistence
│   ├── config.py      #   async engine + session factory
│   ├── models/        #   one module per entity
│   │   ├── base.py    #     declarative Base (shared created_at)
│   │   └── user.py    #     Role enum + User model
│   └── repo/          #   one repository per entity
│       ├── base.py    #     BaseRepo (DI root) + get_repo
│       └── user.py    #     UserRepo
└── workers/           # Celery app + periodic cleanup task
```

**Layering:** `api` → `services` → `database`. The repository (`BaseRepo`) is the
single dependency-injected data-access entrypoint; sub-repos (`repo.users`) hang
off it. Schema is owned by Alembic, never `create_all`.

### Authentication

JWT access + refresh tokens (`PyJWT`, HS256). Each token carries `sub` (user id),
`role`, `exp`, and a `type` claim so `/auth/refresh` rejects access tokens.
Passwords are hashed with `bcrypt`. **Only verified accounts can log in** —
`POST /auth/login` returns `403` until the user completes `POST /auth/verify`.

### Roles

`user` (default) and `admin`. `require_admin` gates admin-only endpoints
(`GET /users`, `GET /users/{id}`, `DELETE /users/{id}`). On `PATCH /users/{id}`
a user may edit only their own profile, and only admins may change a role.

### Verification

On signup a cryptographically-random 6-digit code is generated, stored in
**Redis** with a TTL (`VERIFICATION_CODE_TTL_MINUTES`, default 30) so it expires
automatically, and "sent" via a `Sender`. In dev the `ConsoleSender` logs it.
Swapping to real email (SMTP) or SMS (e.g. Twilio) is a one-file change
implementing the same `Sender` interface and registering it in `get_sender`.
`/auth/verify` looks the code up in Redis (a missing key = expired or never
issued) and deletes it on success — see `app/services/verification/store.py`.

### Automatic cleanup

Celery Beat runs `cleanup_unverified_users` every `CLEANUP_INTERVAL_MINUTES`
(default 60). It deletes users that are still unverified after `CLEANUP_DAYS`
(default **2**, per spec). The task reuses the async repository via `asyncio.run`.

---

## Endpoints

| Method | Path            | Access            | Description                       |
|--------|-----------------|-------------------|-----------------------------------|
| POST   | `/auth/signup`  | public            | Register (unverified)             |
| POST   | `/auth/login`   | public            | Issue tokens (verified users only)|
| POST   | `/auth/refresh` | public (refresh)  | New access token                  |
| POST   | `/auth/verify`  | public            | Confirm account with code         |
| GET    | `/me`           | authenticated     | Current user                      |
| GET    | `/users`        | **admin**         | List users (paginated)            |
| GET    | `/users/{id}`   | **admin**         | Get user by id                    |
| PATCH  | `/users/{id}`   | self or admin     | Partial update                    |
| DELETE | `/users/{id}`   | **admin**         | Delete user                       |

All endpoints have English `summary`/`description` visible in Swagger UI.

---

## Configuration

All via environment variables (see `.env.example`): `DATABASE_URL`, `JWT_SECRET`,
`ACCESS_TOKEN_TTL_MINUTES`, `REFRESH_TOKEN_TTL_DAYS`,
`VERIFICATION_CODE_TTL_MINUTES`, `REDIS_URL`, `CLEANUP_DAYS`,
`CLEANUP_INTERVAL_MINUTES`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.
Secrets live only in `.env`.

---

## Intentional simplifications

Per the spec, simplified areas are flagged in code with notes on how they'd be
hardened given more time:

- **Refresh tokens are stateless** — no server-side allowlist, so no rotation or
  revocation. Production: persist a token/jti record per session and rotate on use.
- **Verification sender is console-only** here; the `Sender` ABC is the seam for
  real email/SMS providers.
- **Celery task uses `asyncio.run`** over the async repo for a single source of
  truth; a high-throughput worker would use a dedicated sync DB engine.
