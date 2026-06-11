#!/bin/sh
# Apply DB migrations, then start the app. Retry upgrade a few times in case
# Postgres is still coming up (compose also gates us on its healthcheck).
set -e

n=0
until alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 10 ]; then
    echo "alembic upgrade failed after $n attempts" >&2
    exit 1
  fi
  echo "DB not ready, retrying migrations ($n)..." >&2
  sleep 2
done

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
