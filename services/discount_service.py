"""
Service layer for discount-related business logic.
"""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import structlog

from models.orm.review import DiscountCode
from models.schemas.order import DiscountCodeCreate, DiscountCodeUpdate, DiscountValidation

logger = structlog.get_logger(__name__)


class DiscountService:
    """Service for discount code operations."""

    async def validate_discount_code(
        self, session: AsyncSession, code: str, cart_total: Decimal, user_id: Optional[UUID] = None
    ) -> DiscountValidation:
        """Validate a discount code and return its applicability."""
        try:
            discount_code = await self.get_discount_by_code(session, code)

            if not discount_code:
                return DiscountValidation(is_valid=False, message="Invalid discount code.")
            
            if not discount_code.is_active:
                return DiscountValidation(is_valid=False, message="This discount code is not active.")

            now = datetime.utcnow()
            if discount_code.valid_from > now:
                return DiscountValidation(is_valid=False, message="Discount is not yet valid.")
            if discount_code.valid_until and discount_code.valid_until < now:
                return DiscountValidation(is_valid=False, message="Discount has expired.")
            
            if discount_code.minimum_order_amount and cart_total < discount_code.minimum_order_amount:
                return DiscountValidation(
                    is_valid=False,
                    message=f"A minimum order total of ${discount_code.minimum_order_amount} is required."
                )

            if discount_code.usage_limit and discount_code.usage_count >= discount_code.usage_limit:
                return DiscountValidation(is_valid=False, message="Discount usage limit has been reached.")

            # Here you would add logic for usage_limit_per_user, which requires tracking usage per user.
            # This is a placeholder for that more complex logic.

            discount_amount = self.calculate_discount(discount_code, cart_total)

            return DiscountValidation(
                is_valid=True,
                message="Discount applied successfully.",
                discount_amount=discount_amount
            )
        except Exception as e:
            logger.error("Error validating discount code", code=code, error=str(e), exc_info=True)
            raise

    def calculate_discount(self, discount_code: DiscountCode, amount: Decimal) -> Decimal:
        """Calculate the discount amount based on the code's type and value."""
        if discount_code.discount_type == "percentage":
            discount = (amount * discount_code.discount_value) / 100
            if discount_code.maximum_discount_amount and discount > discount_code.maximum_discount_amount:
                return discount_code.maximum_discount_amount
            return discount
        elif discount_code.discount_type == "fixed":
            return min(discount_code.discount_value, amount) # Cannot discount more than the total
        return Decimal("0.00")

    async def get_discount_by_code(
        self, session: AsyncSession, code: str
    ) -> Optional[DiscountCode]:
        """Retrieve a discount code by its code string."""
        try:
            result = await session.execute(
                select(DiscountCode).where(DiscountCode.code == code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Error getting discount by code", code=code, error=str(e), exc_info=True)
            raise

    async def get_all_discounts(
        self, session: AsyncSession
    ) -> List[DiscountCode]:
        """Retrieve all discount codes."""
        try:
            result = await session.execute(select(DiscountCode))
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting all discounts", error=str(e), exc_info=True)
            raise

    async def create_discount(
        self, session: AsyncSession, discount_data: DiscountCodeCreate
    ) -> DiscountCode:
        """Create a new discount code."""
        try:
            new_discount = DiscountCode(**discount_data.model_dump())
            session.add(new_discount)
            await session.flush()
            await session.refresh(new_discount)
            logger.info("Discount created", code=new_discount.code)
            return new_discount
        except Exception as e:
            logger.error("Error creating discount", error=str(e), exc_info=True)
            raise

    async def update_discount(
        self, session: AsyncSession, discount_id: UUID, discount_data: DiscountCodeUpdate
    ) -> Optional[DiscountCode]:
        """Update an existing discount code."""
        try:
            discount = await session.get(DiscountCode, discount_id)
            if not discount:
                return None
            
            update_data = discount_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(discount, key, value)

            await session.flush()
            await session.refresh(discount)
            logger.info("Discount updated", code=discount.code)
            return discount
        except Exception as e:
            logger.error("Error updating discount", discount_id=discount_id, error=str(e), exc_info=True)
            raise

    async def delete_discount(self, session: AsyncSession, discount_id: UUID) -> bool:
        """Delete a discount code."""
        try:
            discount = await session.get(DiscountCode, discount_id)
            if not discount:
                return False
            
            await session.delete(discount)
            await session.flush()
            logger.info("Discount deleted", discount_id=discount_id)
            return True
        except Exception as e:
            logger.error("Error deleting discount", discount_id=discount_id, error=str(e), exc_info=True)
            raise

discount_service = DiscountService() 