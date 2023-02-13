"""
Cart API routes.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_async_session
from services.cart_service import cart_service
from middleware.auth import get_current_user
from models.orm.user import User
from models.schemas.cart import (
    CartResponse,
    AddToCartRequest,
    UpdateCartItemRequest,
)
from models.schemas.common import StandardResponse
from middleware.rate_limit import limiter

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/cart", tags=["Cart"])

def _enrich_cart_response(cart: CartResponse) -> CartResponse:
    """Helper to calculate total items and subtotal for the cart response."""
    if cart and cart.items:
        cart.total_items = sum(item.quantity for item in cart.items)
        cart.subtotal = sum(item.total_price for item in cart.items)
    return cart

@router.get(
    "",
    response_model=StandardResponse[CartResponse],
    summary="Get user's cart",
    description="Retrieve the current user's shopping cart.",
)
async def get_cart(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get the current user's cart."""
    try:
        cart = await cart_service.get_cart_by_user_id(session, current_user.id)
        if not cart:
            return StandardResponse(
                success=True,
                message="Cart is empty",
                data=None # Return null data for an empty cart
            )
        
        return StandardResponse(
            success=True,
            message="Cart retrieved successfully",
            data=_enrich_cart_response(cart)
        )
    except Exception as e:
        logger.error("Failed to get cart", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cart",
        )

@router.post(
    "/items",
    response_model=StandardResponse[CartResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
    description="Add a product variant to the user's shopping cart.",
)
@limiter.limit("30/minute")
async def add_item_to_cart(
    request: Request,
    item_data: AddToCartRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Add an item to the cart."""
    try:
        cart = await cart_service.add_item_to_cart(session, current_user, item_data)
        return StandardResponse(
            success=True,
            message="Item added to cart",
            data=_enrich_cart_response(cart)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to add item to cart", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart",
        )

@router.put(
    "/items/{item_id}",
    response_model=StandardResponse[CartResponse],
    summary="Update cart item",
    description="Update the quantity or customizations of an item in the cart.",
)
@limiter.limit("30/minute")
async def update_cart_item(
    request: Request,
    item_id: UUID,
    item_data: UpdateCartItemRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update a cart item."""
    try:
        cart = await cart_service.update_cart_item(
            session, current_user.id, item_id, item_data
        )
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        return StandardResponse(
            success=True,
            message="Cart item updated successfully",
            data=_enrich_cart_response(cart)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Failed to update cart item", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item",
        )

@router.delete(
    "/items/{item_id}",
    response_model=StandardResponse[CartResponse],
    summary="Remove item from cart",
    description="Remove a specific item from the shopping cart.",
)
@limiter.limit("30/minute")
async def remove_cart_item(
    request: Request,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Remove an item from the cart."""
    cart = await cart_service.remove_item_from_cart(
        session, current_user.id, item_id
    )
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    return StandardResponse(
        success=True,
        message="Item removed from cart",
        data=_enrich_cart_response(cart)
    )

@router.delete(
    "",
    response_model=StandardResponse[bool],
    summary="Clear cart",
    description="Remove all items from the user's shopping cart.",
)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Clear all items from the cart."""
    success = await cart_service.clear_cart(session, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found or already empty",
        )
    return StandardResponse(
        success=True,
        message="Cart cleared successfully",
        data=True
    ) 