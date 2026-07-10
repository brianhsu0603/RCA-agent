from celery import Celery

from app.config import settings
from app.logging_config import setup_logging
from app.sentry_init import init_sentry

setup_logging()
init_sentry()

celery_app = Celery(
    "rca_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(task_track_started=True)
