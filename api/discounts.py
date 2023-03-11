"""
Discount API routes.
"""
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_async_session
from services.discount_service import discount_service
from middleware.auth import require_admin
from models.schemas.order import (
    DiscountCodeCreate,
    DiscountCodeUpdate,
    DiscountCodeResponse,
    DiscountValidation,
)
from models.schemas.common import StandardResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/discounts", tags=["Discounts"])

class DiscountValidationRequest(BaseModel):
    code: str = Field(..., max_length=50)
    cart_total: Decimal = Field(..., ge=0)

@router.post(
    "/validate",
    response_model=StandardResponse[DiscountValidation],
    summary="Validate a discount code",
    description="Checks if a discount code is valid and returns the discount amount.",
)
async def validate_discount(
    request: Request,
    validation_data: DiscountValidationRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Validate a discount code against a cart total."""
    try:
        validation_result = await discount_service.validate_discount_code(
            session, validation_data.code, validation_data.cart_total
        )
        return StandardResponse(
            success=True,
            message="Validation check complete.",
            data=validation_result
        )
    except Exception as e:
        logger.error("Failed to validate discount", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate discount code.",
        )

# Admin-only CRUD endpoints
@router.post(
    "",
    response_model=StandardResponse[DiscountCodeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a discount code",
    description="Create a new discount code. Requires admin privileges.",
    dependencies=[Depends(require_admin())],
)
async def create_discount(
    discount_data: DiscountCodeCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Admin: Create a discount code."""
    discount = await discount_service.create_discount(session, discount_data)
    return StandardResponse(
        success=True,
        message="Discount code created successfully.",
        data=discount
    )

@router.get(
    "",
    response_model=StandardResponse[List[DiscountCodeResponse]],
    summary="List all discount codes",
    description="Retrieve a list of all discount codes. Requires admin privileges.",
    dependencies=[Depends(require_admin())],
)
async def list_discounts(session: AsyncSession = Depends(get_async_session)):
    """Admin: List all discount codes."""
    discounts = await discount_service.get_all_discounts(session)
    return StandardResponse(
        success=True,
        message="Discounts retrieved successfully.",
        data=discounts
    )

@router.put(
    "/{discount_id}",
    response_model=StandardResponse[DiscountCodeResponse],
    summary="Update a discount code",
    description="Update an existing discount code. Requires admin privileges.",
    dependencies=[Depends(require_admin())],
)
async def update_discount(
    discount_id: UUID,
    discount_data: DiscountCodeUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Admin: Update a discount code."""
    discount = await discount_service.update_discount(session, discount_id, discount_data)
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount code not found.")
    return StandardResponse(
        success=True,
        message="Discount updated successfully.",
        data=discount
    )

@router.delete(
    "/{discount_id}",
    response_model=StandardResponse[bool],
    status_code=status.HTTP_200_OK,
    summary="Delete a discount code",
    description="Delete a discount code. Requires admin privileges.",
    dependencies=[Depends(require_admin())],
)
async def delete_discount(
    discount_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Admin: Delete a discount code."""
    success = await discount_service.delete_discount(session, discount_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount code not found.")
    return StandardResponse(
        success=True,
        message="Discount deleted successfully.",
        data=True
    ) 