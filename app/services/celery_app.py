from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "workout_analyzer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.services.celery_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    'app.services.celery_tasks.process_video_task': {'queue': 'video_processing'},
    'app.services.celery_tasks.generate_report_task': {'queue': 'report_generation'},
}

# Configure queues
celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'video_processing': {
        'exchange': 'video_processing',
        'routing_key': 'video_processing',
    },
    'report_generation': {
        'exchange': 'report_generation',
        'routing_key': 'report_generation',
    },
}

if __name__ == '__main__':
    celery_app.start()