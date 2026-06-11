"""Celery application + Beat schedule.

Run the worker:   celery -A app.workers.celery_app.celery worker -l info
Run the beat:     celery -A app.workers.celery_app.celery beat -l info

Both are wired as separate services in docker-compose.yml. The schedule fires
`cleanup_unverified_users` every CLEANUP_INTERVAL_MINUTES.
"""

from celery import Celery
from celery.schedules import crontab  # noqa: F401  (handy for finer schedules)

from ..config import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    CLEANUP_INTERVAL_MINUTES,
)

celery = Celery(
    "orbit",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery.conf.update(
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-unverified-users": {
            "task": "app.workers.tasks.cleanup_unverified_users",
            # Interval in seconds; configurable via CLEANUP_INTERVAL_MINUTES.
            "schedule": CLEANUP_INTERVAL_MINUTES * 60,
        },
    },
)
