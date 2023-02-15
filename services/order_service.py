"""
Service layer for order-related business logic.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
import shortuuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import structlog

from models.orm.order import Order, OrderItem
from models.orm.cart import Cart
from models.orm.user import User, Address
from models.orm.review import DiscountCode
from models.schemas.order import CheckoutRequest
from services.cart_service import cart_service
from services.discount_service import discount_service
from services.user_service import UserService

logger = structlog.get_logger(__name__)


class OrderService:
    """Service for order operations."""

    async def create_order_from_cart(
        self, session: AsyncSession, user: User, checkout_data: CheckoutRequest
    ) -> Order:
        """Create an order from the user's shopping cart."""
        try:
            cart = await cart_service.get_cart_by_user_id(session, user.id)
            if not cart or not cart.items:
                raise ValueError("Cannot create an order from an empty cart.")

            # Resolve shipping and billing addresses
            shipping_address = await self._get_address_data(session, user.id, checkout_data.shipping_address_id)
            billing_address = await self._get_address_data(session, user.id, checkout_data.billing_address_id, shipping_address)
            
            # Calculate pricing
            subtotal = sum(item.total_price for item in cart.items)
            discount_amount = await self._validate_and_get_discount(session, checkout_data.discount_code, subtotal)
            shipping_amount = self._calculate_shipping() # Placeholder
            tax_amount = self._calculate_tax(subtotal - discount_amount) # Placeholder
            total_amount = subtotal - discount_amount + shipping_amount + tax_amount

            # Create the order
            new_order = Order(
                user_id=user.id,
                order_number=self.generate_order_number(),
                status="pending",
                payment_status="pending",
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                shipping_address=shipping_address,
                billing_address=billing_address,
                shipping_method=checkout_data.shipping_method,
                payment_method=checkout_data.payment_method,
                customer_notes=checkout_data.customer_notes
            )

            # Create order items from cart items
            for item in cart.items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_variant_id=item.product_variant_id,
                    product_name=item.product_variant.product.name,
                    variant_name=item.product_variant.name,
                    sku=item.product_variant.sku,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    customizations=item.customizations,
                )
                new_order.items.append(order_item)
            
            session.add(new_order)
            
            # Clear the cart
            await cart_service.clear_cart(session, user.id)

            await session.flush()
            await session.refresh(new_order)
            
            logger.info("Order created successfully", order_id=new_order.id, user_id=user.id)
            return new_order

        except ValueError as e:
            logger.warning("Value error creating order", error=str(e))
            raise
        except Exception as e:
            logger.error("Error creating order from cart", error=str(e), exc_info=True)
            raise

    async def get_user_orders(self, session: AsyncSession, user_id: UUID) -> List[Order]:
        """Retrieve all orders for a specific user."""
        result = await session.execute(
            select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_order_details(self, session: AsyncSession, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Retrieve a single order's details if it belongs to the user."""
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(selectinload(Order.items).joinedload(OrderItem.product_variant))
        )
        return result.scalar_one_or_none()
    
    def generate_order_number(self) -> str:
        """Generate a unique, human-readable order number."""
        return f"ORD-{shortuuid.ShortUUID().random(length=8).upper()}"

    async def _get_address_data(self, session: AsyncSession, user_id: UUID, address_id: UUID, default_address: Optional[Dict] = None) -> Dict:
        """Fetch address from DB and return as dict, or return default."""
        if address_id:
            user_service = UserService(session)
            address = await user_service.get_user_address_by_id(user_id, address_id)
            if not address:
                raise ValueError(f"Address with ID {address_id} not found for this user.")
            return {
                "first_name": address.first_name,
                "last_name": address.last_name,
                "street_address_1": address.street_address_1,
                "city": address.city,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": address.country,
                "phone": address.phone,
            }
        if default_address:
            return default_address
        raise ValueError("A valid shipping address must be provided.")

    async def _validate_and_get_discount(self, session: AsyncSession, code: Optional[str], subtotal: Decimal) -> Decimal:
        """Validate a discount code and return the discount amount."""
        if not code:
            return Decimal("0.00")
        validation = await discount_service.validate_discount_code(session, code, subtotal)
        if validation.is_valid:
            return validation.discount_amount
        raise ValueError(validation.message)

    def _calculate_shipping(self) -> Decimal:
        """Placeholder for shipping calculation logic."""
        return Decimal("9.99") # Flat rate for now

    def _calculate_tax(self, taxable_amount: Decimal) -> Decimal:
        """Placeholder for tax calculation logic."""
        return taxable_amount * Decimal("0.08") # 8% tax for now


order_service = OrderService() 