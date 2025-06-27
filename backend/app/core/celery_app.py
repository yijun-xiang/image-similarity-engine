from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "image_similarity",
    broker=f"amqp://admin:admin@localhost:5672//",
    backend="redis://localhost:6379/1",
    include=["app.tasks.image_tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    result_expires=3600,
    enable_utc=True,
    timezone="UTC",
    beat_schedule={},
)

class CeleryConfig:
    broker_url = f"amqp://admin:admin@localhost:5672//"
    result_backend = "redis://localhost:6379/1"
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    result_accept_content = ["json"]
    task_track_started = True
    task_time_limit = 300
    task_soft_time_limit = 240

celery_app.config_from_object(CeleryConfig)
