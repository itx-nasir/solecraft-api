"""
Email tasks for Celery worker using SendGrid.
"""

from typing import Optional, Dict, Any
import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent, PlainTextContent

from workers.celery_app import celery_app
from core.config import settings

logger = structlog.get_logger(__name__)


class EmailService:
    """SendGrid email service."""
    
    def __init__(self):
        self.client = SendGridAPIClient(api_key=settings.sendgrid_api_key)
        self.from_email = From(settings.email_from, settings.email_from_name)
    
    def send_email(
        self,
        to_email: str,
        subject_text: str,
        html_content: str,
        text_content: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send email using SendGrid."""
        try:
            # Create message
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=Subject(subject_text),
                html_content=HtmlContent(html_content)
            )
            
            # Add plain text content if provided
            if text_content:
                message.plain_text_content = PlainTextContent(text_content)
            
            # Send email
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


def get_email_service() -> EmailService:
    """Get email service instance."""
    return EmailService()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: str, email: str, first_name: str):
    """Send welcome email to new user."""
    try:
        email_service = get_email_service()
        subject = "Welcome to SoleCraft!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to SoleCraft</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .feature-list {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .feature-list ul {{ margin: 0; padding-left: 20px; }}
                .feature-list li {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to SoleCraft, {first_name}!</h1>
                    <p>Your journey to custom shoes begins here</p>
                </div>
                
                <div class="content">
                    <h2>Thank you for joining SoleCraft! 👋</h2>
                    <p>We're excited to help you create the perfect pair of shoes that matches your unique style and personality.</p>
                    
                    <div class="feature-list">
                        <h3>What's Next?</h3>
                        <ul>
                            <li><strong>Explore our collection</strong> - Browse hundreds of customizable shoe designs</li>
                            <li><strong>Design your perfect pair</strong> - Use our interactive design tools</li>
                            <li><strong>Track your orders</strong> - Monitor your custom shoes from creation to delivery</li>
                            <li><strong>Join our community</strong> - Share your designs and get inspired by others</li>
                        </ul>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="{settings.frontend_url}" class="btn">Start Designing Now</a>
                    </p>
                    
                    <p>If you have any questions, our customer support team is here to help 24/7!</p>
                    <p>Happy designing!</p>
                </div>
                
                <div class="footer">
                    <p><strong>The SoleCraft Team</strong></p>
                    <p><small>This email was sent to {email}. If you didn't create an account, please ignore this email.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to SoleCraft, {first_name}!

        Thank you for creating an account with SoleCraft, your premier destination for customizable shoes.
        We're excited to help you create the perfect pair of shoes that matches your unique style.

        What's Next?
        • Explore our extensive collection of customizable shoes
        • Use our design tools to create your perfect pair
        • Track your orders and manage your account
        • Join our community of shoe designers

        Start designing: {settings.frontend_url}

        If you have any questions, our customer support team is here to help!
        Happy designing!

        Best regards,
        The SoleCraft Team

        ---
        This email was sent to {email}. If you didn't create an account, please ignore this email.
        """
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if not success:
            logger.warning("Welcome email failed, retrying", user_id=user_id, email=email)
            raise Exception("Failed to send welcome email")
        
        logger.info("Welcome email sent successfully", user_id=user_id, email=email)
        
    except Exception as e:
        logger.error("Welcome email task failed", error=str(e), user_id=user_id, email=email)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(self, user_id: str, email: str, verification_token: str):
    """Send email verification link."""
    try:
        email_service = get_email_service()
        verification_url = f"{settings.frontend_url}/verify-email?token={verification_token}"
        subject = "Verify Your SoleCraft Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }}
                .btn {{ display: inline-block; padding: 15px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
                .btn:hover {{ background: #218838; }}
                .verification-code {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }}
                .warning {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Verify Your Email Address</h1>
                    <p>Just one more step to complete your registration</p>
                </div>
                
                <div class="content">
                    <h2>Almost there!</h2>
                    <p>Thank you for signing up with SoleCraft! To complete your registration and secure your account, please verify your email address.</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="btn">✅ Verify Email Address</a>
                    </div>
                    
                    <div class="verification-code">
                        <p><strong>Alternative method:</strong> If the button doesn't work, copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; font-family: monospace;">{verification_url}</p>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⏰ Important:</strong> This verification link will expire in 24 hours for security reasons.</p>
                    </div>
                    
                    <p>Once verified, you'll have full access to all SoleCraft features including order tracking and design saving.</p>
                    
                    <p>If you didn't create an account with SoleCraft, please ignore this email and your email address will not be added to our system.</p>
                </div>
                
                <div class="footer">
                    <p><strong>The SoleCraft Team</strong></p>
                    <p><small>This verification email was sent to {email}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Verify Your Email Address

        Thank you for signing up with SoleCraft! To complete your registration, please verify your email address.

        Copy and paste this link into your browser to verify your account:
        {verification_url}

        This verification link will expire in 24 hours for security reasons.

        Once verified, you'll have full access to all SoleCraft features.

        If you didn't create an account with SoleCraft, please ignore this email.

        Best regards,
        The SoleCraft Team

        ---
        This verification email was sent to {email}
        """
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if not success:
            logger.warning("Verification email failed, retrying", user_id=user_id, email=email)
            raise Exception("Failed to send verification email")
        
        logger.info("Verification email sent successfully", user_id=user_id, email=email)
        
    except Exception as e:
        logger.error("Verification email task failed", error=str(e), user_id=user_id, email=email)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_order_confirmation_email(self, user_id: str, email: str, order_id: str, order_total: float):
    """Send order confirmation email."""
    try:
        email_service = get_email_service()
        subject = f"Order Confirmation - SoleCraft #{order_id}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Order Confirmation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #007bff 0%, #6610f2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }}
                .order-details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .order-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .total {{ font-size: 20px; font-weight: bold; color: #28a745; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Order Confirmed!</h1>
                    <p>Thank you for your SoleCraft order</p>
                </div>
                
                <div class="content">
                    <h2>Your order has been received!</h2>
                    <p>Thank you for your order! We've received your custom shoe order and our craftsmen are already getting to work.</p>
                    
                    <div class="order-details">
                        <h3>Order Details</h3>
                        <p><strong>Order Number:</strong> <span class="order-number">#{order_id}</span></p>
                        <p><strong>Total Amount:</strong> <span class="total">${order_total:.2f}</span></p>
                        <p><strong>Order Date:</strong> {str(datetime.now().strftime('%B %d, %Y'))}</p>
                    </div>
                    
                    <h3>What happens next?</h3>
                    <ul>
                        <li><strong>Order Processing:</strong> 1-2 business days</li>
                        <li><strong>Custom Manufacturing:</strong> 2-3 weeks</li>
                        <li><strong>Quality Check:</strong> 1-2 days</li>
                        <li><strong>Shipping:</strong> 3-5 business days</li>
                    </ul>
                    
                    <p>You'll receive another email with tracking information when your order ships.</p>
                    
                    <div style="text-align: center;">
                        <a href="{settings.frontend_url}/orders/{order_id}" class="btn">Track Your Order</a>
                        <a href="{settings.frontend_url}/contact" class="btn">Contact Support</a>
                    </div>
                    
                    <p>Thank you for choosing SoleCraft for your custom footwear needs!</p>
                </div>
                
                <div class="footer">
                    <p><strong>The SoleCraft Team</strong></p>
                    <p><small>Order confirmation sent to {email}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Order Confirmation - SoleCraft #{order_id}

        Thank you for your order! We've received your custom shoe order and our craftsmen are already getting to work.

        Order Details:
        • Order Number: #{order_id}
        • Total Amount: ${order_total:.2f}
        • Order Date: {str(datetime.now().strftime('%B %d, %Y'))}

        What happens next?
        • Order Processing: 1-2 business days
        • Custom Manufacturing: 2-3 weeks
        • Quality Check: 1-2 days
        • Shipping: 3-5 business days

        You'll receive tracking information when your order ships.

        Track your order: {settings.frontend_url}/orders/{order_id}

        Thank you for choosing SoleCraft!

        Best regards,
        The SoleCraft Team

        ---
        Order confirmation sent to {email}
        """
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if not success:
            logger.warning("Order confirmation email failed, retrying", user_id=user_id, email=email, order_id=order_id)
            raise Exception("Failed to send order confirmation email")
        
        logger.info("Order confirmation email sent successfully", user_id=user_id, email=email, order_id=order_id)
        
    except Exception as e:
        logger.error("Order confirmation email task failed", error=str(e), user_id=user_id, email=email, order_id=order_id)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (self.request.retries + 1))
        raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, email: str, reset_token: str):
    """Send password reset email."""
    try:
        email_service = get_email_service()
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        subject = "Reset Your SoleCraft Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }}
                .btn {{ display: inline-block; padding: 15px 30px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
                .warning {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                .security-note {{ background: #d1ecf1; padding: 15px; border-left: 4px solid #bee5eb; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                    <p>Reset your SoleCraft account password</p>
                </div>
                
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>We received a request to reset the password for your SoleCraft account associated with this email address.</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="btn">🔑 Reset Password</a>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⏰ Important:</strong> This password reset link will expire in 1 hour for security reasons.</p>
                    </div>
                    
                    <div class="security-note">
                        <p><strong>🛡️ Security Note:</strong> If you didn't request this password reset, please ignore this email. Your account remains secure and no changes have been made.</p>
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; font-family: monospace;">{reset_url}</p>
                </div>
                
                <div class="footer">
                    <p><strong>The SoleCraft Team</strong></p>
                    <p><small>Password reset requested for {email}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request

        We received a request to reset the password for your SoleCraft account.

        Reset your password by clicking this link:
        {reset_url}

        This link will expire in 1 hour for security reasons.

        If you didn't request this password reset, please ignore this email. Your account remains secure.

        Best regards,
        The SoleCraft Team

        ---
        Password reset requested for {email}
        """
        
        success = email_service.send_email(email, subject, html_content, text_content)
        
        if not success:
            logger.warning("Password reset email failed, retrying", email=email)
            raise Exception("Failed to send password reset email")
        
        logger.info("Password reset email sent successfully", email=email)
        
    except Exception as e:
        logger.error("Password reset email task failed", error=str(e), email=email)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise


# Import datetime for order confirmation
from datetime import datetime


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_low_inventory_alert(self, alert_data: dict):
    """Send low inventory alert to admin."""
    try:
        email_service = get_email_service()
        
        variant_id = alert_data.get("variant_id")
        product_name = alert_data.get("product_name", "Unknown Product")
        variant_name = alert_data.get("variant_name", "Unknown Variant")
        current_stock = alert_data.get("current_stock", 0)
        
        subject = f"🚨 Low Inventory Alert - {product_name}"
        admin_email = settings.admin_email or "admin@solecraft.com"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Low Inventory Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }}
                .alert-box {{ background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                .product-details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .stock-critical {{ color: #dc3545; font-weight: bold; font-size: 18px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Low Inventory Alert</h1>
                    <p>Immediate attention required</p>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <h3>⚠️ Stock Level Critical</h3>
                        <p>One of your products is running low on inventory and needs immediate restocking.</p>
                    </div>
                    
                    <div class="product-details">
                        <h3>Product Details</h3>
                        <p><strong>Product:</strong> {product_name}</p>
                        <p><strong>Variant:</strong> {variant_name}</p>
                        <p><strong>Current Stock:</strong> <span class="stock-critical">{current_stock} units</span></p>
                        <p><strong>Variant ID:</strong> {variant_id}</p>
                    </div>
                    
                    <div class="alert-box">
                        <h3>🎯 Action Required</h3>
                        <p><strong>Please restock this item immediately</strong> to prevent stockouts and lost sales.</p>
                        <ul>
                            <li>Review sales velocity for this product</li>
                            <li>Contact suppliers for urgent restocking</li>
                            <li>Consider temporarily hiding the product if stock reaches zero</li>
                            <li>Update inventory management system</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{settings.frontend_url}/admin/inventory" class="btn">Manage Inventory</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>SoleCraft Inventory Management System</strong></p>
                    <p><small>This alert was generated automatically at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        🚨 LOW INVENTORY ALERT
        
        One of your products is running low on inventory and needs immediate restocking.
        
        Product Details:
        • Product: {product_name}
        • Variant: {variant_name}
        • Current Stock: {current_stock} units
        • Variant ID: {variant_id}
        
        ACTION REQUIRED:
        Please restock this item immediately to prevent stockouts and lost sales.
        
        Steps to take:
        1. Review sales velocity for this product
        2. Contact suppliers for urgent restocking
        3. Consider temporarily hiding the product if stock reaches zero
        4. Update inventory management system
        
        Manage inventory: {settings.frontend_url}/admin/inventory
        
        ---
        SoleCraft Inventory Management System
        Alert generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        success = email_service.send_email(admin_email, subject, html_content, text_content)
        
        if not success:
            logger.warning("Low inventory alert failed, retrying", variant_id=variant_id)
            raise Exception("Failed to send low inventory alert")
        
        logger.info("Low inventory alert sent successfully", variant_id=variant_id, current_stock=current_stock)
        
    except Exception as e:
        logger.error("Low inventory alert task failed", error=str(e), alert_data=alert_data)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        raise 