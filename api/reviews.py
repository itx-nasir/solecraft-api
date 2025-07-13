"""
Review API routes.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_async_session
from services.review_service import review_service
from middleware.auth import get_current_active_user, get_current_user
from models.orm.user import User
from models.schemas.common import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    StandardResponse,
)
from middleware.rate_limit import limiter

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post(
    "",
    response_model=StandardResponse[ReviewResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a product review",
    description="Create a new review for a product. User must be authenticated.",
)
@limiter.limit("10/hour")
async def create_review(
    request: Request,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Submit a product review."""
    try:
        review = await review_service.create_review(session, current_user, review_data)
        return StandardResponse(
            success=True,
            message="Review submitted successfully.",
            data=review
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to create review", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit review.",
        )

@router.get(
    "/product/{product_id}",
    response_model=StandardResponse[List[ReviewResponse]],
    summary="Get product reviews",
    description="Get all approved reviews for a specific product.",
)
async def get_product_reviews(
    product_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get all reviews for a product."""
    try:
        reviews = await review_service.get_reviews_for_product(session, product_id)
        return StandardResponse(
            success=True,
            message="Reviews retrieved successfully.",
            data=reviews
        )
    except Exception as e:
        logger.error("Failed to get reviews", product_id=product_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reviews.",
        )

@router.put(
    "/{review_id}",
    response_model=StandardResponse[ReviewResponse],
    summary="Update a review",
    description="Update a review that you have submitted.",
)
@limiter.limit("10/hour")
async def update_review(
    review_id: UUID,
    review_data: ReviewUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update an existing review."""
    try:
        review = await review_service.update_review(session, review_id, current_user.id, review_data)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or you do not have permission to edit it.")
        return StandardResponse(
            success=True,
            message="Review updated successfully.",
            data=review
        )
    except Exception as e:
        logger.error("Failed to update review", review_id=review_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review.",
        )

@router.delete(
    "/{review_id}",
    response_model=StandardResponse[bool],
    status_code=status.HTTP_200_OK,
    summary="Delete a review",
    description="Delete a review that you have submitted.",
)
async def delete_review(
    review_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete a review."""
    success = await review_service.delete_review(session, review_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or you do not have permission to delete it.")
    return StandardResponse(
        success=True,
        message="Review deleted successfully.",
        data=True
    ) 