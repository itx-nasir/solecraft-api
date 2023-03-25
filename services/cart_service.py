"""
Service layer for cart-related business logic.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
import structlog

from models.orm.cart import Cart, CartItem
from models.orm.product import Product
from models.orm.user import User
from models.schemas.cart import AddToCartRequest, UpdateCartItemRequest

logger = structlog.get_logger(__name__)


class CartService:
    """Service for cart operations."""

    async def get_cart_by_user_id(
        self, session: AsyncSession, user_id: UUID
    ) -> Optional[Cart]:
        """Retrieve a cart by user ID, including items and product variants."""
        try:
            result = await session.execute(
                select(Cart)
                .where(Cart.user_id == user_id)
                .options(
                    selectinload(Cart.items).options(
                        joinedload(CartItem.product)
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                "Error retrieving cart by user ID",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise

    async def _calculate_item_prices(
        self,
        session: AsyncSession,
        product_id: UUID,
        quantity: int,
    ) -> (Decimal, Decimal, Dict[str, Any]):
        """Calculate unit price, total price, and format customizations."""
        product = await session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found")

        unit_price = product.base_price
        customization_price = Decimal("0.00")
        formatted_customizations = {}

        # Remove all logic and references to ProductVariant, product_variant, and customizations throughout the file.

        unit_price += customization_price
        total_price = unit_price * quantity
        return unit_price, total_price, formatted_customizations

    async def add_item_to_cart(
        self, session: AsyncSession, user: User, item_data: AddToCartRequest
    ) -> Cart:
        """Add an item to the user's cart. Creates a cart if one doesn't exist."""
        try:
            cart = await self.get_cart_by_user_id(session, user.id)
            if not cart:
                cart = Cart(user_id=user.id, session_id=user.session_id)
                session.add(cart)
                await session.flush()

            # Check if a similar item (same variant and customizations) already exists
            existing_item = next(
                (
                    item
                    for item in cart.items
                    if item.product_id == item_data.product_id
                    # This comparison is simplistic. A real implementation needs a robust way
                    # to compare customization dictionaries.
                ),
                None,
            )

            if existing_item:
                existing_item.quantity += item_data.quantity
                _, total_price, _ = await self._calculate_item_prices(
                    session,
                    existing_item.product_id,
                    existing_item.quantity,
                )
                existing_item.total_price = total_price

            else:
                unit_price, total_price, formatted_customizations = await self._calculate_item_prices(
                    session,
                    item_data.product_id,
                    item_data.quantity,
                )
                new_item = CartItem(
                    cart_id=cart.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )
                cart.items.append(new_item)
                session.add(new_item)

            await session.flush()
            await session.refresh(cart)
            logger.info("Item added to cart", cart_id=cart.id, user_id=user.id)
            return cart
        except ValueError as e:
            logger.warning("Value error adding item to cart", error=str(e))
            raise
        except Exception as e:
            logger.error("Error adding item to cart", error=str(e), exc_info=True)
            raise

    async def update_cart_item(
        self,
        session: AsyncSession,
        user_id: UUID,
        item_id: UUID,
        item_data: UpdateCartItemRequest
    ) -> Optional[Cart]:
        """Update a cart item's quantity or customizations."""
        try:
            cart = await self.get_cart_by_user_id(session, user_id)
            if not cart:
                return None
            
            item_to_update = await session.get(CartItem, item_id)
            if not item_to_update or item_to_update.cart_id != cart.id:
                return None

            item_to_update.quantity = item_data.quantity
            unit_price, total_price, formatted_customizations = await self._calculate_item_prices(
                session,
                item_to_update.product_id,
                item_data.quantity,
            )
            item_to_update.unit_price = unit_price
            item_to_update.total_price = total_price
            item_to_update.customizations = formatted_customizations

            await session.flush()
            await session.refresh(cart)
            logger.info("Cart item updated", item_id=item_id, cart_id=cart.id)
            return cart
        except ValueError as e:
            logger.warning("Value error updating cart item", error=str(e))
            raise
        except Exception as e:
            logger.error("Error updating cart item", error=str(e), exc_info=True)
            raise

    async def remove_item_from_cart(
        self, session: AsyncSession, user_id: UUID, item_id: UUID
    ) -> Optional[Cart]:
        """Remove an item from the cart."""
        try:
            cart = await self.get_cart_by_user_id(session, user_id)
            if not cart:
                return None
            
            item_to_remove = await session.get(CartItem, item_id)

            if item_to_remove and item_to_remove.cart_id == cart.id:
                await session.delete(item_to_remove)
                await session.flush()
                await session.refresh(cart)
                logger.info("Item removed from cart", item_id=item_id, cart_id=cart.id)
                return cart
            return None # Item not found or doesn't belong to the cart
        except Exception as e:
            logger.error("Error removing item from cart", error=str(e), exc_info=True)
            raise

    async def clear_cart(
        self, session: AsyncSession, user_id: UUID
    ) -> bool:
        """Clear all items from a user's cart."""
        try:
            cart = await self.get_cart_by_user_id(session, user_id)
            if cart:
                for item in cart.items:
                    await session.delete(item)
                await session.flush()
                logger.info("Cart cleared", cart_id=cart.id, user_id=user_id)
                return True
            return False
        except Exception as e:
            logger.error("Error clearing cart", error=str(e), exc_info=True)
            raise

cart_service = CartService() 