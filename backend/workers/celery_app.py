"""Celery application configuration for async TLF generation."""
from celery import Celery

from backend.core.config import settings

celery_app = Celery(
    "tlf_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_soft_time_limit=600,    # 10 min
    task_time_limit=900,          # 15 min
    worker_max_tasks_per_child=5,
    task_routes={
        "tlf.generate": {"queue": "default"},
    },
    # Auto-discover tasks from backend.workers.tasks
    imports=["backend.workers.tasks"],
)
