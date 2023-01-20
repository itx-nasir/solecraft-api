"""
Cleanup-related Celery tasks for maintaining database hygiene.
"""

from typing import Optional, List, Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func
from datetime import datetime, timedelta

from workers.celery_app import celery_app
from infrastructure.database import get_async_session
from models.orm.user import User
from models.orm.cart import Cart, CartItem
from models.orm.order import Order
from models.orm.review import Review

logger = structlog.get_logger(__name__)


@celery_app.task
def cleanup_guest_users() -> dict:
    """
    Cleanup guest users and their associated data that are older than 7 days.
    
    Returns:
        dict: Cleanup result with counts
    """
    try:
        logger.info("Starting guest users cleanup")
        
        import asyncio
        
        async def _cleanup_guests():
            async with get_async_session() as session:
                # Find guest users older than 7 days
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                
                result = await session.execute(
                    select(User).where(
                        and_(
                            User.is_guest == True,
                            User.created_at < cutoff_date
                        )
                    )
                )
                guest_users = result.scalars().all()
                
                deleted_users = 0
                deleted_carts = 0
                deleted_orders = 0
                
                for user in guest_users:
                    # Check if user has any completed orders
                    orders_result = await session.execute(
                        select(func.count(Order.id)).where(
                            and_(
                                Order.user_id == user.id,
                                Order.payment_status == "completed"
                            )
                        )
                    )
                    completed_orders_count = orders_result.scalar()
                    
                    # Don't delete users with completed orders
                    if completed_orders_count > 0:
                        logger.info(
                            "Skipping guest user with completed orders",
                            user_id=user.id,
                            completed_orders=completed_orders_count
                        )
                        continue
                    
                    # Delete associated cart items first
                    await session.execute(
                        delete(CartItem).where(
                            CartItem.cart_id.in_(
                                select(Cart.id).where(Cart.user_id == user.id)
                            )
                        )
                    )
                    
                    # Delete carts
                    carts_deleted_result = await session.execute(
                        delete(Cart).where(Cart.user_id == user.id)
                    )
                    deleted_carts += carts_deleted_result.rowcount
                    
                    # Delete incomplete orders
                    orders_deleted_result = await session.execute(
                        delete(Order).where(
                            and_(
                                Order.user_id == user.id,
                                Order.payment_status.in_(["pending", "failed"])
                            )
                        )
                    )
                    deleted_orders += orders_deleted_result.rowcount
                    
                    # Delete the user
                    await session.delete(user)
                    deleted_users += 1
                
                await session.commit()
                
                logger.info(
                    "Guest users cleanup completed",
                    deleted_users=deleted_users,
                    deleted_carts=deleted_carts,
                    deleted_orders=deleted_orders
                )
                
                return {
                    "status": "success",
                    "deleted_users": deleted_users,
                    "deleted_carts": deleted_carts,
                    "deleted_orders": deleted_orders,
                    "cutoff_date": cutoff_date.isoformat()
                }
        
        result = asyncio.run(_cleanup_guests())
        return result
        
    except Exception as exc:
        logger.error("Failed to cleanup guest users", error=str(exc))
        raise exc


@celery_app.task
def cleanup_abandoned_carts() -> dict:
    """
    Cleanup abandoned carts that haven't been updated in 30 days.
    
    Returns:
        dict: Cleanup result with counts
    """
    try:
        logger.info("Starting abandoned carts cleanup")
        
        import asyncio
        
        async def _cleanup_carts():
            async with get_async_session() as session:
                # Find abandoned carts older than 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                # First, delete cart items for abandoned carts
                cart_items_result = await session.execute(
                    delete(CartItem).where(
                        CartItem.cart_id.in_(
                            select(Cart.id).where(Cart.updated_at < cutoff_date)
                        )
                    )
                )
                deleted_cart_items = cart_items_result.rowcount
                
                # Then delete the carts themselves
                carts_result = await session.execute(
                    delete(Cart).where(Cart.updated_at < cutoff_date)
                )
                deleted_carts = carts_result.rowcount
                
                await session.commit()
                
                logger.info(
                    "Abandoned carts cleanup completed",
                    deleted_carts=deleted_carts,
                    deleted_cart_items=deleted_cart_items
                )
                
                return {
                    "status": "success",
                    "deleted_carts": deleted_carts,
                    "deleted_cart_items": deleted_cart_items,
                    "cutoff_date": cutoff_date.isoformat()
                }
        
        result = asyncio.run(_cleanup_carts())
        return result
        
    except Exception as exc:
        logger.error("Failed to cleanup abandoned carts", error=str(exc))
        raise exc


@celery_app.task
def cleanup_failed_orders() -> dict:
    """
    Cleanup failed orders older than 90 days and their associated data.
    
    Returns:
        dict: Cleanup result with counts
    """
    try:
        logger.info("Starting failed orders cleanup")
        
        import asyncio
        
        async def _cleanup_failed_orders():
            async with get_async_session() as session:
                # Find failed orders older than 90 days
                cutoff_date = datetime.utcnow() - timedelta(days=90)
                
                result = await session.execute(
                    select(Order).where(
                        and_(
                            Order.payment_status.in_(["failed", "cancelled"]),
                            Order.created_at < cutoff_date
                        )
                    )
                )
                failed_orders = result.scalars().all()
                
                deleted_orders = 0
                
                for order in failed_orders:
                    # Delete the order (cascade should handle order items)
                    await session.delete(order)
                    deleted_orders += 1
                
                await session.commit()
                
                logger.info(
                    "Failed orders cleanup completed",
                    deleted_orders=deleted_orders
                )
                
                return {
                    "status": "success",
                    "deleted_orders": deleted_orders,
                    "cutoff_date": cutoff_date.isoformat()
                }
        
        result = asyncio.run(_cleanup_failed_orders())
        return result
        
    except Exception as exc:
        logger.error("Failed to cleanup failed orders", error=str(exc))
        raise exc


@celery_app.task
def cleanup_old_sessions() -> dict:
    """
    Cleanup old session data and tokens.
    Note: This would typically work with a sessions table if implemented.
    
    Returns:
        dict: Cleanup result
    """
    try:
        logger.info("Starting old sessions cleanup")
        
        # In a real implementation, you would clean up:
        # - Expired JWT tokens from a blacklist table
        # - Session data from Redis or database
        # - Old password reset tokens
        # - Old email verification tokens
        
        # For now, this is a placeholder
        logger.info("Session cleanup completed (placeholder)")
        
        return {
            "status": "success",
            "message": "Session cleanup completed (placeholder implementation)"
        }
        
    except Exception as exc:
        logger.error("Failed to cleanup old sessions", error=str(exc))
        raise exc


@celery_app.task
def cleanup_old_logs() -> dict:
    """
    Cleanup old application logs if stored in database.
    
    Returns:
        dict: Cleanup result
    """
    try:
        logger.info("Starting old logs cleanup")
        
        # In a real implementation, you would clean up:
        # - Old log entries from a logs table
        # - Old audit trail entries
        # - Old error logs
        
        # For now, this is a placeholder
        logger.info("Logs cleanup completed (placeholder)")
        
        return {
            "status": "success",
            "message": "Logs cleanup completed (placeholder implementation)"
        }
        
    except Exception as exc:
        logger.error("Failed to cleanup old logs", error=str(exc))
        raise exc


@celery_app.task
def optimize_database() -> dict:
    """
    Perform database optimization tasks like updating statistics and reindexing.
    
    Returns:
        dict: Optimization result
    """
    try:
        logger.info("Starting database optimization")
        
        import asyncio
        
        async def _optimize_db():
            async with get_async_session() as session:
                # In PostgreSQL, you might run ANALYZE to update statistics
                # Note: This is a simplified example
                
                # Get table statistics
                tables_result = await session.execute(
                    """
                    SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    """
                )
                table_stats = tables_result.fetchall()
                
                stats_info = []
                for stat in table_stats:
                    stats_info.append({
                        "table": f"{stat.schemaname}.{stat.tablename}",
                        "inserts": stat.n_tup_ins,
                        "updates": stat.n_tup_upd,
                        "deletes": stat.n_tup_del
                    })
                
                logger.info(
                    "Database optimization completed",
                    table_count=len(stats_info)
                )
                
                return {
                    "status": "success",
                    "table_stats": stats_info,
                    "optimized_at": datetime.utcnow().isoformat()
                }
        
        result = asyncio.run(_optimize_db())
        return result
        
    except Exception as exc:
        logger.error("Failed to optimize database", error=str(exc))
        raise exc


@celery_app.task
def generate_cleanup_report() -> dict:
    """
    Generate a report on database cleanup activities.
    
    Returns:
        dict: Cleanup report
    """
    try:
        logger.info("Generating cleanup report")
        
        import asyncio
        
        async def _generate_report():
            async with get_async_session() as session:
                # Get counts of various entities
                users_result = await session.execute(
                    select(func.count(User.id)).where(User.is_guest == True)
                )
                guest_users_count = users_result.scalar()
                
                registered_users_result = await session.execute(
                    select(func.count(User.id)).where(User.is_guest == False)
                )
                registered_users_count = registered_users_result.scalar()
                
                carts_result = await session.execute(
                    select(func.count(Cart.id))
                )
                total_carts = carts_result.scalar()
                
                orders_result = await session.execute(
                    select(
                        Order.order_status,
                        func.count(Order.id).label("count")
                    ).group_by(Order.order_status)
                )
                order_status_counts = {row.order_status: row.count for row in orders_result}
                
                # Calculate abandoned carts (not updated in 7 days)
                abandoned_cutoff = datetime.utcnow() - timedelta(days=7)
                abandoned_carts_result = await session.execute(
                    select(func.count(Cart.id)).where(Cart.updated_at < abandoned_cutoff)
                )
                abandoned_carts_count = abandoned_carts_result.scalar()
                
                report = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "users": {
                        "guest_users": guest_users_count,
                        "registered_users": registered_users_count,
                        "total": guest_users_count + registered_users_count
                    },
                    "carts": {
                        "total": total_carts,
                        "abandoned": abandoned_carts_count
                    },
                    "orders": order_status_counts,
                    "recommendations": []
                }
                
                # Add cleanup recommendations
                if abandoned_carts_count > 100:
                    report["recommendations"].append(
                        "Consider running abandoned cart cleanup - high count detected"
                    )
                
                if guest_users_count > 1000:
                    report["recommendations"].append(
                        "Consider running guest user cleanup - high count detected"
                    )
                
                logger.info("Cleanup report generated successfully", report=report)
                return {"status": "success", "report": report}
        
        result = asyncio.run(_generate_report())
        return result
        
    except Exception as exc:
        logger.error("Failed to generate cleanup report", error=str(exc))
        raise exc 