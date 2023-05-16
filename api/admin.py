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
    # Eagerly load all relationships before conversion
    await session.refresh(order, attribute_names=["items", "user", "discount_code"])
    # Manually build dict for OrderResponse
    order_dict = {
        "id": order.id,
        "user_id": order.user_id,
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "subtotal": order.subtotal,
        "tax_amount": order.tax_amount,
        "shipping_amount": order.shipping_amount,
        "discount_amount": order.discount_amount,
        "total_amount": order.total_amount,
        "shipping_address": order.shipping_address,
        "billing_address": order.billing_address,
        "shipping_method": order.shipping_method,
        "tracking_number": order.tracking_number,
        "payment_method": order.payment_method,
        "payment_provider": order.payment_provider,
        "confirmed_at": order.confirmed_at,
        "shipped_at": order.shipped_at,
        "delivered_at": order.delivered_at,
        "notes": order.notes,
        "customer_notes": order.customer_notes,
        "items": [
            {
                "id": item.id,
                "order_id": item.order_id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "sku": item.sku,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in order.items
        ],
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }
    order_response = OrderResponse(**order_dict)
    return StandardResponse(
        success=True,
        message="Order status updated successfully.",
        data=order_response
    ) 