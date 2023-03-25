"""
Service for handling background tasks, such as sending emails and processing data.
"""

from typing import Optional, Dict, Any
import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent, PlainTextContent

from core.config import settings

logger = structlog.get_logger(__name__)


class EmailService:
    """SendGrid email service."""
    
    def __init__(self):
        if not settings.sendgrid_api_key:
            raise ValueError("SendGrid API key is not configured.")
        self.client = SendGridAPIClient(api_key=settings.sendgrid_api_key)
        self.from_email = From(settings.email_from, settings.email_from_name)
    
    def send_email(
        self,
        to_email: str,
        subject_text: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email using SendGrid."""
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=Subject(subject_text),
                html_content=HtmlContent(html_content)
            )
            
            if text_content:
                message.plain_text_content = PlainTextContent(text_content)
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info("Email sent successfully", 
                           to_email=to_email, 
                           subject=subject_text,
                           status_code=response.status_code)
                return True
            else:
                logger.error("SendGrid returned error", 
                            status_code=response.status_code,
                            body=response.body)
                return False
                
        except Exception as e:
            logger.error("Failed to send email", 
                        error=str(e), 
                        to_email=to_email, 
                        subject=subject_text)
            return False


def send_welcome_email(user_id: str, email: str, first_name: str):
    """Send welcome email to new user."""
    try:
        email_service = EmailService()
        subject = "Welcome to SoleCraft!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to SoleCraft</title>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to SoleCraft, {first_name}!</h1>
                <p>Your journey to custom shoes begins here</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to SoleCraft, {first_name}!
        Thank you for creating an account with SoleCraft.
        """
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if success:
            logger.info("Welcome email sent successfully", user_id=user_id, email=email)
        else:
            logger.warning("Failed to send welcome email", user_id=user_id, email=email)
        
    except Exception as e:
        logger.error("Welcome email task failed", error=str(e), user_id=user_id, email=email)


def send_verification_email(user_id: str, email: str, verification_token: str):
    """Send email verification link."""
    try:
        email_service = EmailService()
        verification_url = f"{settings.frontend_url}/auth/verify-email?token={verification_token}"
        subject = "Verify Your SoleCraft Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
        </head>
        <body>
            <div class="container">
                 <h1>Verify Your Email Address</h1>
                 <p>Click the link below to verify your email address.</p>
                 <a href="{verification_url}">Verify Email Address</a>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Verify Your Email Address
        Copy and paste this link into your browser to verify your account:
        {verification_url}
        """
        
        success = email_service.send_email(email, subject, html_content, text_content)

        if success:
            logger.info("Verification email sent successfully", user_id=user_id, email=email)
        else:
            logger.warning("Failed to send verification email", user_id=user_id, email=email)

    except Exception as e:
        logger.error("Verification email task failed", error=str(e), user_id=user_id, email=email)


def send_order_confirmation_email(user_id: str, email: str, order_id: str, order_total: float):
    """Send order confirmation email."""
    try:
        email_service = EmailService()
        subject = f"Your SoleCraft Order Confirmation #{order_id}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Order Confirmed!</h1>
            <p>Thank you for your order. Your order number is {order_id}.</p>
            <p>Total: ${order_total:.2f}</p>
        </body>
        </html>
        """
        
        text_content = f"Order Confirmed! Your order number is {order_id}. Total: ${order_total:.2f}"
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if success:
            logger.info("Order confirmation email sent successfully", order_id=order_id, user_id=user_id)
        else:
            logger.warning("Failed to send order confirmation email", order_id=order_id, user_id=user_id)
            
    except Exception as e:
        logger.error("Order confirmation email task failed", error=str(e), order_id=order_id)


def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email."""
    try:
        email_service = EmailService()
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        subject = "Reset Your SoleCraft Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Password Reset Request</h1>
            <p>Click the link below to reset your password.</p>
            <a href="{reset_url}">Reset Password</a>
        </body>
        </html>
        """
        
        text_content = f"Reset your password using this link: {reset_url}"
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if success:
            logger.info("Password reset email sent successfully", email=email)
        else:
            logger.warning("Failed to send password reset email", email=email)
            
    except Exception as e:
        logger.error("Password reset email task failed", error=str(e), email=email)


def send_low_inventory_alert(alert_data: dict):
    """Send low inventory alert."""
    try:
        email_service = EmailService()
        subject = "Low Inventory Alert"
        product_name = alert_data.get("product_name", "N/A")
        current_stock = alert_data.get("current_stock", "N/A")
        
        html_content = f"""
        <h1>Low Inventory Alert</h1>
        <p>Product: {product_name}</p>
        <p>Current Stock: {current_stock}</p>
        """
        
        text_content = f"Low Inventory Alert: {product_name} is low on stock ({current_stock} left)."
        
        # This alert should probably go to an admin email address
        admin_email = settings.admin_email 
        if not admin_email:
            logger.warning("Admin email not set, cannot send low inventory alert.")
            return

        success = email_service.send_email(admin_email, subject, html_content, text_content)
        
        if success:
            logger.info("Low inventory alert sent successfully", alert_data=alert_data)
        else:
            logger.warning("Failed to send low inventory alert", alert_data=alert_data)

    except Exception as e:
        logger.error("Low inventory alert task failed", error=str(e), alert_data=alert_data)


# Order Processing and Cleanup Tasks

from core.database import get_async_session
from models.orm.order import Order, OrderItem
from models.orm.product import Product
from models.orm.user import User
from models.orm.cart import Cart, CartItem
from sqlalchemy import select, delete, and_, func
from datetime import datetime, timedelta
import asyncio


async def process_order_payment(order_id: int):
    """
    Process payment for an order.
    """
    try:
        logger.info("Processing payment for order", order_id=order_id)
        
        async with get_async_session() as session:
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            
            if not order or order.payment_status != "pending":
                logger.warning("Order not found or payment already processed", order_id=order_id)
                return

            # Simulate payment processing delay
            await asyncio.sleep(2)
            
            order.payment_status = "completed"
            order.order_status = "processing"
            order.updated_at = datetime.utcnow()
            
            await session.commit()
            
            if order.user_id:
                user_result = await session.execute(select(User).where(User.id == order.user_id))
                user = user_result.scalar_one_or_none()
                if user and user.email:
                    send_order_confirmation_email(
                        str(order.user_id), 
                        user.email, 
                        str(order_id), 
                        float(order.total_amount)
                    )
            
            logger.info("Payment processed successfully", order_id=order_id)
            await update_inventory_after_order(order_id)

    except Exception as e:
        logger.error("Failed to process payment", order_id=order_id, error=str(e))
        async with get_async_session() as session:
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            if order:
                order.payment_status = "failed"
                order.order_status = "cancelled"
                await session.commit()


async def update_inventory_after_order(order_id: int):
    """
    Update product inventory after successful order.
    """
    try:
        logger.info("Updating inventory for order", order_id=order_id)
        async with get_async_session() as session:
            result = await session.execute(
                select(OrderItem).where(OrderItem.order_id == order_id)
            )
            order_items = result.scalars().all()
            
            low_stock_alerts = []
            
            for item in order_items:
                product_result = await session.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                
                if product:
                    product.stock_quantity -= item.quantity
                    if product.stock_quantity <= 5:
                        low_stock_alerts.append({
                            "product_id": product.id,
                            "product_name": product.name,
                            "current_stock": product.stock_quantity
                        })
            
            await session.commit()
            
            for alert in low_stock_alerts:
                send_low_inventory_alert(alert)
            
            logger.info("Inventory updated successfully", order_id=order_id)

    except Exception as e:
        logger.error("Failed to update inventory", order_id=order_id, error=str(e))


# Scheduled Tasks

async def process_pending_orders():
    """
    Periodic task to process orders that are stuck in pending status.
    """
    try:
        logger.info("Processing pending orders")
        async with get_async_session() as session:
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
            
            for order in pending_orders:
                if order.created_at < datetime.utcnow() - timedelta(hours=24):
                    order.payment_status = "failed"
                    order.order_status = "cancelled"
                    logger.info("Cancelled stale order", order_id=order.id)
                else:
                    # In a simplified setup, we just log this. 
                    # A more complex retry could be added if needed.
                    logger.info("Order is still pending", order_id=order.id)
            
            await session.commit()
            logger.info(f"Checked {len(pending_orders)} pending orders.")

    except Exception as e:
        logger.error("Failed to process pending orders", error=str(e))


async def check_low_inventory():
    """
    Periodic task to check for low inventory.
    """
    try:
        logger.info("Checking for low inventory")
        async with get_async_session() as session:
            result = await session.execute(
                select(Product).where(Product.stock_quantity <= 5)
            )
            low_stock_products = result.scalars().all()
            
            for product in low_stock_products:
                send_low_inventory_alert({
                    "product_id": product.id,
                    "product_name": product.name,
                    "current_stock": product.stock_quantity
                })
        logger.info(f"Found {len(low_stock_products)} products with low stock.")

    except Exception as e:
        logger.error("Failed to check low inventory", error=str(e))


async def cleanup_guest_users():
    """
    Cleanup guest users and their associated data that are older than 7 days.
    """
    try:
        logger.info("Starting guest users cleanup")
        async with get_async_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            result = await session.execute(
                select(User).where(and_(User.is_guest == True, User.created_at < cutoff_date))
            )
            guest_users = result.scalars().all()
            
            for user in guest_users:
                # Basic check, can be expanded
                await session.delete(user)

            await session.commit()
            logger.info(f"Cleaned up {len(guest_users)} guest users.")

    except Exception as e:
        logger.error("Failed to cleanup guest users", error=str(e))


async def cleanup_abandoned_carts():
    """
    Cleanup abandoned carts that haven't been updated in 30 days.
    """
    try:
        logger.info("Starting abandoned carts cleanup")
        async with get_async_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            await session.execute(
                delete(CartItem).where(
                    CartItem.cart_id.in_(select(Cart.id).where(Cart.updated_at < cutoff_date))
                )
            )
            
            result = await session.execute(
                delete(Cart).where(Cart.updated_at < cutoff_date)
            )
            
            await session.commit()
            logger.info(f"Cleaned up {result.rowcount} abandoned carts.")

    except Exception as e:
        logger.error("Failed to cleanup abandoned carts", error=str(e)) 