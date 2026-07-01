from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()
celery_app = Celery(
    "nestly",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    beat_schedule={
        "scrape-property24-morning": {
            "task": "scrape.run_property24",
            "schedule": crontab(hour=6, minute=0),  # 06:00 SAST
            "kwargs": {"max_pages": 50},
        },
        "scrape-property24-evening": {
            "task": "scrape.run_property24",
            "schedule": crontab(hour=18, minute=0),  # 18:00 SAST
            "kwargs": {"max_pages": 50},
        },
        "enrich-listings-morning": {
            "task": "scrape.enrich_listings",
            "schedule": crontab(hour=6, minute=30),  # 06:30 SAST, after scrape
            "kwargs": {"batch_size": 100},
        },
        "enrich-listings-evening": {
            "task": "scrape.enrich_listings",
            "schedule": crontab(hour=18, minute=30),  # 18:30 SAST, after scrape
            "kwargs": {"batch_size": 100},
        },
    },
    timezone="Africa/Johannesburg",
)

# Celery CLI discovery expects an attribute named `app` or `celery`.
# This allows: `celery -A app.tasks worker --loglevel=info`
app = celery_app
celery = celery_app

# Import tasks so they are registered with Celery
import app.tasks.search  # noqa: E402, F401
import app.tasks.scrape  # noqa: E402, F401
