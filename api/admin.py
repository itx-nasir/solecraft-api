"""
Admin API routes.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_async_session
from services.admin_service import admin_service
from middleware.auth import require_admin
from models.schemas.order import OrderResponse, OrderUpdate, OrderListResponse
from models.schemas.common import StandardResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin())])


@router.get(
    "/dashboard",
    response_model=StandardResponse[dict],
    summary="Get dashboard statistics",
    description="Retrieve key statistics for the admin dashboard.",
)
async def get_dashboard_stats(session: AsyncSession = Depends(get_async_session)):
    """Get dashboard statistics."""
    stats = await admin_service.get_dashboard_statistics(session)
    return StandardResponse(
        success=True,
        message="Dashboard statistics retrieved successfully.",
        data=stats
    )

@router.get(
    "/orders",
    response_model=StandardResponse[List[OrderListResponse]],
    summary="List all orders",
    description="Get a list of all orders in the system.",
)
async def list_all_orders(session: AsyncSession = Depends(get_async_session)):
    """List all orders."""
    orders = await admin_service.list_all_orders(session)
    return StandardResponse(
        success=True,
        message="All orders retrieved successfully.",
        data=orders
    )

@router.put(
    "/orders/{order_id}/status",
    response_model=StandardResponse[OrderResponse],
    summary="Update order status",
    description="Update the status of a specific order.",
)
async def update_order_status(
    order_id: UUID,
    status_update: OrderUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Update an order's status."""
    order = await admin_service.update_order_status(session, order_id, status_update)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    # Eagerly load items relationship before conversion
    await session.refresh(order, attribute_names=["items"])
    order_response = OrderResponse.model_validate(order)
    return StandardResponse(
        success=True,
        message="Order status updated successfully.",
        data=order_response
    ) 