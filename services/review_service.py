"""
Service layer for review-related business logic.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import structlog

from models.orm.review import Review
from models.orm.user import User
from models.orm.order import Order, OrderItem
from models.schemas.common import ReviewCreate, ReviewUpdate

logger = structlog.get_logger(__name__)


class ReviewService:
    """Service for review operations."""

    async def create_review(
        self, session: AsyncSession, user: User, review_data: ReviewCreate
    ) -> Review:
        """Create a new product review."""
        try:
            # Check if the user has purchased the product
            has_purchased = await self._check_verified_purchase(session, user.id, review_data.product_id)
            
            # Check for existing review
            existing_review = await self.get_review_by_user_and_product(session, user.id, review_data.product_id)
            if existing_review:
                raise ValueError("You have already submitted a review for this product.")

            new_review = Review(
                user_id=user.id,
                product_id=review_data.product_id,
                rating=review_data.rating,
                title=review_data.title,
                comment=review_data.comment,
                is_verified_purchase=has_purchased,
                is_approved=True # Auto-approve for now
            )
            session.add(new_review)
            await session.flush()
            await session.refresh(new_review)
            logger.info("Review created", review_id=new_review.id, user_id=user.id)
            return new_review
        except ValueError as e:
            logger.warning("Could not create review", error=str(e), user_id=user.id)
            raise
        except Exception as e:
            logger.error("Error creating review", error=str(e), exc_info=True)
            raise

    async def get_reviews_for_product(
        self, session: AsyncSession, product_id: UUID
    ) -> List[Review]:
        """Retrieve all approved reviews for a specific product."""
        try:
            result = await session.execute(
                select(Review)
                .where(Review.product_id == product_id, Review.is_approved == True)
                .options(selectinload(Review.user))
                .order_by(Review.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Error getting reviews for product", product_id=product_id, error=str(e), exc_info=True)
            raise
            
    async def get_review_by_user_and_product(self, session: AsyncSession, user_id: UUID, product_id: UUID) -> Optional[Review]:
        """Get a single review by user and product ID."""
        result = await session.execute(
            select(Review).where(Review.user_id == user_id, Review.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def update_review(
        self, session: AsyncSession, review_id: UUID, user_id: UUID, update_data: ReviewUpdate
    ) -> Optional[Review]:
        """Update an existing review."""
        try:
            review = await session.get(Review, review_id)
            if not review or review.user_id != user_id:
                return None
            
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(review, key, value)
            
            await session.flush()
            await session.refresh(review)
            logger.info("Review updated", review_id=review.id)
            return review
        except Exception as e:
            logger.error("Error updating review", review_id=review_id, error=str(e), exc_info=True)
            raise

    async def delete_review(self, session: AsyncSession, review_id: UUID, user_id: UUID) -> bool:
        """Delete a user's review."""
        try:
            review = await session.get(Review, review_id)
            if not review or review.user_id != user_id:
                return False
            
            await session.delete(review)
            await session.flush()
            logger.info("Review deleted", review_id=review_id)
            return True
        except Exception as e:
            logger.error("Error deleting review", review_id=review_id, error=str(e), exc_info=True)
            raise
            
    async def _check_verified_purchase(self, session: AsyncSession, user_id: UUID, product_id: UUID) -> bool:
        """Check if the user has a completed order for the given product."""
        result = await session.execute(
            select(OrderItem.id)
            .join(Order)
            .join(OrderItem.product_variant)
            .where(
                Order.user_id == user_id,
                Order.payment_status == "completed",
                # This check should be on product_id, not variant
                # A user might buy different variants of the same product
                OrderItem.product_variant.has(product_id=product_id)
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

review_service = ReviewService() 