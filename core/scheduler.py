"""
Scheduler configuration for periodic background tasks.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import structlog

from services.background_tasks_service import (
    cleanup_guest_users,
    cleanup_abandoned_carts,
    process_pending_orders,
    check_low_inventory,
)

logger = structlog.get_logger(__name__)

scheduler = AsyncIOScheduler()

def initialize_scheduler():
    """
    Initializes and starts the scheduler, adding all periodic jobs.
    """
    try:
        logger.info("Initializing scheduler...")
        
        # Add jobs from the former celery beat schedule
        scheduler.add_job(
            cleanup_guest_users,
            trigger="cron",
            hour=2,
            minute=0,
            id="cleanup_guest_users",
            name="Clean up guest users daily at 2 AM",
            replace_existing=True,
        )
        scheduler.add_job(
            cleanup_abandoned_carts,
            trigger="cron",
            hour="*/6",
            minute=0,
            id="cleanup_abandoned_carts",
            name="Clean up abandoned carts every 6 hours",
            replace_existing=True,
        )
        scheduler.add_job(
            process_pending_orders,
            trigger="cron",
            minute="*/30",
            id="process_pending_orders",
            name="Process pending orders every 30 minutes",
            replace_existing=True,
        )
        scheduler.add_job(
            check_low_inventory,
            trigger="cron",
            hour=8,
            minute=0,
            id="check_low_inventory",
            name="Check for low inventory daily at 8 AM",
            replace_existing=True,
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully.")
        
    except Exception as e:
        logger.error("Failed to initialize or start scheduler", error=str(e))

def shutdown_scheduler():
    """
    Shuts down the scheduler.
    """
    if scheduler.running:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully.") 