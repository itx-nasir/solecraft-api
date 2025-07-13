"""
Order API routes.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_async_session
from services.order_service import order_service
from middleware.auth import get_current_active_user
from models.orm.user import User
from models.schemas.order import (
    CheckoutRequest,
    OrderResponse,
    OrderListResponse,
)
from models.schemas.common import StandardResponse, PaginatedResponse, PaginationParams
from middleware.rate_limit import limiter

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/checkout",
    response_model=StandardResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create an order from cart",
    description="Initiate the checkout process, converting the user's cart into a formal order.",
)
@limiter.limit("5/minute")
async def checkout(
    request: Request,
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create an order from the current user's cart."""
    try:
        order = await order_service.create_order_from_cart(session, current_user, checkout_data)
        return StandardResponse(
            success=True,
            message="Order created successfully.",
            data=order
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Checkout failed", error=str(e), user_id=current_user.id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during checkout.",
        )

@router.get(
    "",
    response_model=StandardResponse[List[OrderListResponse]],
    summary="Get user's order history",
    description="Retrieve a list of all orders placed by the current user.",
)
async def get_orders(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get the current user's order history."""
    try:
        orders = await order_service.get_user_orders(session, current_user.id)
        return StandardResponse(
            success=True,
            message="Orders retrieved successfully.",
            data=orders
        )
    except Exception as e:
        logger.error("Failed to get orders", error=str(e), user_id=current_user.id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders.",
        )

@router.get(
    "/{order_id}",
    response_model=StandardResponse[OrderResponse],
    summary="Get order details",
    description="Retrieve detailed information about a specific order.",
)
async def get_order_details(
    order_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get details for a single order."""
    try:
        order = await order_service.get_order_details(session, order_id, current_user.id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        return StandardResponse(
            success=True,
            message="Order details retrieved successfully.",
            data=order
        )
    except Exception as e:
        logger.error("Failed to get order details", order_id=order_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order details.",
        ) 