"""
Celery application configuration for async tasks.
"""

from celery import Celery
from celery.schedules import crontab
import structlog
import platform

from core.config import settings

logger = structlog.get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "solecraft",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.email_tasks",
        "workers.order_tasks",
        "workers.cleanup_tasks",
    ]
)

# Windows-specific settings
if platform.system() == "Windows":
    celery_app.conf.worker_pool = "solo"
    celery_app.conf.broker_connection_retry_on_startup = True

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Simplified task routing - all tasks go to default queue for now
    # task_routes={
    #     "workers.email_tasks.*": {"queue": "emails"},
    #     "workers.order_tasks.*": {"queue": "orders"},
    #     "workers.cleanup_tasks.*": {"queue": "cleanup"},
    # },
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Cleanup old guest users every day at 2 AM
        "cleanup-guest-users": {
            "task": "workers.cleanup_tasks.cleanup_guest_users",
            "schedule": crontab(hour=2, minute=0),
        },
        # Cleanup incomplete carts every 6 hours
        "cleanup-abandoned-carts": {
            "task": "workers.cleanup_tasks.cleanup_abandoned_carts",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        # Process pending orders every 30 minutes
        "process-pending-orders": {
            "task": "workers.order_tasks.process_pending_orders",
            "schedule": crontab(minute="*/30"),
        },
        # Update inventory alerts daily at 8 AM
        "inventory-alerts": {
            "task": "workers.order_tasks.check_low_inventory",
            "schedule": crontab(hour=8, minute=0),
        },
    },
    beat_schedule_filename="celerybeat-schedule",
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    logger.info(f"Request: {self.request!r}")
    return f"Debug task executed: {self.request.id}"


if __name__ == "__main__":
    celery_app.start() 