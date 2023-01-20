"""
Order-related Celery tasks for background processing.
"""

from typing import Optional, List
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta

from workers.celery_app import celery_app
from infrastructure.database import get_async_session
from models.orm.order import Order, OrderItem
from models.orm.product import ProductVariant
from models.orm.user import User
from workers.email_tasks import send_order_confirmation_email, send_low_inventory_alert

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_order_payment(self, order_id: int) -> dict:
    """
    Process payment for an order.
    
    Args:
        order_id: ID of the order to process payment for
        
    Returns:
        dict: Payment processing result
    """
    try:
        logger.info("Processing payment for order", order_id=order_id)
        
        # Simulate payment processing
        # In a real implementation, you would integrate with payment providers
        # like Stripe, PayPal, etc.
        
        import asyncio
        
        async def _process_payment():
            async with get_async_session() as session:
                # Get order
                result = await session.execute(
                    select(Order).where(Order.id == order_id)
                )
                order = result.scalar_one_or_none()
                
                if not order:
                    raise ValueError(f"Order {order_id} not found")
                
                if order.payment_status != "pending":
                    logger.warning(
                        "Order payment already processed", 
                        order_id=order_id,
                        current_status=order.payment_status
                    )
                    return {"status": "already_processed", "order_id": order_id}
                
                # Simulate payment processing delay
                await asyncio.sleep(2)
                
                # Update order status
                order.payment_status = "completed"
                order.order_status = "processing"
                order.updated_at = datetime.utcnow()
                
                await session.commit()
                
                # Send confirmation email
                if order.user_id:
                    # Get user details for email
                    user_result = await session.execute(
                        select(User).where(User.id == order.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user and user.email:
                        send_order_confirmation_email.delay(
                            str(order.user_id), 
                            user.email, 
                            str(order_id), 
                            float(order.total_amount)
                        )
                
                logger.info("Payment processed successfully", order_id=order_id)
                return {"status": "success", "order_id": order_id}
        
        result = asyncio.run(_process_payment())
        return result
        
    except Exception as exc:
        logger.error(
            "Failed to process payment", 
            order_id=order_id, 
            error=str(exc),
            retry_count=self.request.retries
        )
        
        if self.request.retries < self.max_retries:
            # Retry with exponential backoff
            countdown = 2 ** self.request.retries * 60  # 1min, 2min, 4min
            raise self.retry(countdown=countdown, exc=exc)
        
        # Final failure - update order status
        import asyncio
        async def _mark_failed():
            async with get_async_session() as session:
                result = await session.execute(
                    select(Order).where(Order.id == order_id)
                )
                order = result.scalar_one_or_none()
                if order:
                    order.payment_status = "failed"
                    order.order_status = "cancelled"
                    await session.commit()
        
        asyncio.run(_mark_failed())
        raise exc


@celery_app.task(bind=True)
def update_inventory_after_order(self, order_id: int) -> dict:
    """
    Update product inventory after successful order.
    
    Args:
        order_id: ID of the order
        
    Returns:
        dict: Inventory update result
    """
    try:
        logger.info("Updating inventory for order", order_id=order_id)
        
        import asyncio
        
        async def _update_inventory():
            async with get_async_session() as session:
                # Get order items
                result = await session.execute(
                    select(OrderItem)
                    .where(OrderItem.order_id == order_id)
                    .join(Order)
                    .where(Order.payment_status == "completed")
                )
                order_items = result.scalars().all()
                
                updated_variants = []
                low_stock_alerts = []
                
                for item in order_items:
                    # Get product variant
                    variant_result = await session.execute(
                        select(ProductVariant)
                        .where(ProductVariant.id == item.product_variant_id)
                    )
                    variant = variant_result.scalar_one_or_none()
                    
                    if variant:
                        # Update stock
                        variant.stock_quantity -= item.quantity
                        updated_variants.append({
                            "variant_id": variant.id,
                            "previous_stock": variant.stock_quantity + item.quantity,
                            "new_stock": variant.stock_quantity,
                            "quantity_sold": item.quantity
                        })
                        
                        # Check for low stock
                        if variant.stock_quantity <= 5:  # Low stock threshold
                            low_stock_alerts.append({
                                "variant_id": variant.id,
                                "product_name": variant.product.name if variant.product else "Unknown",
                                "variant_name": variant.name,
                                "current_stock": variant.stock_quantity
                            })
                
                await session.commit()
                
                # Send low stock alerts
                for alert in low_stock_alerts:
                    send_low_inventory_alert.delay(alert)
                
                logger.info(
                    "Inventory updated successfully", 
                    order_id=order_id,
                    updated_variants=len(updated_variants),
                    low_stock_alerts=len(low_stock_alerts)
                )
                
                return {
                    "status": "success",
                    "order_id": order_id,
                    "updated_variants": updated_variants,
                    "low_stock_alerts": low_stock_alerts
                }
        
        result = asyncio.run(_update_inventory())
        return result
        
    except Exception as exc:
        logger.error(
            "Failed to update inventory", 
            order_id=order_id, 
            error=str(exc)
        )
        raise exc


@celery_app.task
def process_pending_orders() -> dict:
    """
    Periodic task to process orders that are stuck in pending status.
    """
    try:
        logger.info("Processing pending orders")
        
        import asyncio
        
        async def _process_pending():
            async with get_async_session() as session:
                # Find orders pending for more than 1 hour
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                result = await session.execute(
                    select(Order).where(
                        and_(
                            Order.payment_status == "pending",
                            Order.created_at < cutoff_time
                        )
                    )
                )
                pending_orders = result.scalars().all()
                
                processed_count = 0
                cancelled_count = 0
                
                for order in pending_orders:
                    # Cancel orders pending for more than 24 hours
                    if order.created_at < datetime.utcnow() - timedelta(hours=24):
                        order.payment_status = "failed"
                        order.order_status = "cancelled"
                        cancelled_count += 1
                        logger.info("Cancelled stale order", order_id=order.id)
                    else:
                        # Retry payment processing
                        process_order_payment.delay(order.id)
                        processed_count += 1
                        logger.info("Retrying payment for order", order_id=order.id)
                
                if cancelled_count > 0 or processed_count > 0:
                    await session.commit()
                
                logger.info(
                    "Pending orders processed",
                    processed=processed_count,
                    cancelled=cancelled_count
                )
                
                return {
                    "status": "success",
                    "processed": processed_count,
                    "cancelled": cancelled_count
                }
        
        result = asyncio.run(_process_pending())
        return result
        
    except Exception as exc:
        logger.error("Failed to process pending orders", error=str(exc))
        raise exc


@celery_app.task
def check_low_inventory() -> dict:
    """
    Periodic task to check for low inventory and send alerts.
    """
    try:
        logger.info("Checking low inventory")
        
        import asyncio
        
        async def _check_inventory():
            async with get_async_session() as session:
                # Find variants with low stock
                result = await session.execute(
                    select(ProductVariant)
                    .where(ProductVariant.stock_quantity <= 5)
                    .where(ProductVariant.is_active == True)
                )
                low_stock_variants = result.scalars().all()
                
                alerts_sent = 0
                
                for variant in low_stock_variants:
                    alert_data = {
                        "variant_id": variant.id,
                        "product_name": variant.product.name if variant.product else "Unknown",
                        "variant_name": variant.name,
                        "current_stock": variant.stock_quantity
                    }
                    
                    send_low_inventory_alert.delay(alert_data)
                    alerts_sent += 1
                
                logger.info(
                    "Low inventory check completed",
                    low_stock_variants=len(low_stock_variants),
                    alerts_sent=alerts_sent
                )
                
                return {
                    "status": "success",
                    "low_stock_variants": len(low_stock_variants),
                    "alerts_sent": alerts_sent
                }
        
        result = asyncio.run(_check_inventory())
        return result
        
    except Exception as exc:
        logger.error("Failed to check inventory", error=str(exc))
        raise exc


@celery_app.task(bind=True)
def generate_order_report(self, start_date: str, end_date: str) -> dict:
    """
    Generate order report for a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        dict: Order report data
    """
    try:
        logger.info("Generating order report", start_date=start_date, end_date=end_date)
        
        import asyncio
        from datetime import datetime
        
        async def _generate_report():
            async with get_async_session() as session:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                # Get order statistics
                result = await session.execute(
                    select(
                        func.count(Order.id).label("total_orders"),
                        func.sum(Order.total_amount).label("total_revenue"),
                        func.avg(Order.total_amount).label("average_order_value")
                    ).where(
                        and_(
                            Order.created_at >= start_dt,
                            Order.created_at <= end_dt,
                            Order.payment_status == "completed"
                        )
                    )
                )
                stats = result.one()
                
                # Get order status breakdown
                status_result = await session.execute(
                    select(
                        Order.order_status,
                        func.count(Order.id).label("count")
                    ).where(
                        and_(
                            Order.created_at >= start_dt,
                            Order.created_at <= end_dt
                        )
                    ).group_by(Order.order_status)
                )
                status_breakdown = {row.order_status: row.count for row in status_result}
                
                report_data = {
                    "period": {"start": start_date, "end": end_date},
                    "total_orders": stats.total_orders or 0,
                    "total_revenue": float(stats.total_revenue or 0),
                    "average_order_value": float(stats.average_order_value or 0),
                    "status_breakdown": status_breakdown,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                logger.info("Order report generated successfully", report_data=report_data)
                return {"status": "success", "report": report_data}
        
        result = asyncio.run(_generate_report())
        return result
        
    except Exception as exc:
        logger.error(
            "Failed to generate order report", 
            start_date=start_date,
            end_date=end_date,
            error=str(exc)
        )
        raise exc 