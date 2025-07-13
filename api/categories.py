"""
Category API routes.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_async_session
from services.category_service import category_service
from middleware.auth import require_admin
from models.schemas.product import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from models.schemas.common import StandardResponse
from middleware.rate_limit import limiter

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/categories", tags=["Categories"])

# TODO: Replace require_admin with a granular permission system, e.g., require_permission("category:create")

@router.post(
    "",
    response_model=StandardResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Create a new product category. Requires admin privileges.",
    dependencies=[Depends(require_admin())],
)
@limiter.limit("10/minute")
async def create_category(
    request: Request,
    category_data: CategoryCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new category."""
    try:
        category = await category_service.create_category(session, category_data)
        return StandardResponse(
            success=True,
            message="Category created successfully",
            data=category
        )
    except Exception as e:
        logger.error("Failed to create category", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category",
        )

@router.get(
    "",
    response_model=StandardResponse[List[CategoryResponse]],
    summary="List all categories",
    description="Get a list of all product categories, including nested children.",
)
async def list_categories(
    session: AsyncSession = Depends(get_async_session),
):
    """Retrieve all categories."""
    try:
        categories = await category_service.get_all_categories(session)
        return StandardResponse(
            success=True,
            message="Categories retrieved successfully",
            data=categories
        )
    except Exception as e:
        logger.error("Failed to list categories", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list categories",
        )

@router.get(
    "/{category_id}",
    response_model=StandardResponse[CategoryResponse],
    summary="Get a single category",
    description="Get detailed information about a single category by its ID.",
)
async def get_category(
    category_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Get a single category by its UUID."""
    category = await category_service.get_category_by_id(session, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return StandardResponse(
        success=True,
        message="Category found",
        data=category
    )

@router.put(
    "/{category_id}",
    response_model=StandardResponse[CategoryResponse],
    summary="Update a category",
    description="Update an existing category's information. Requires admin privileges.",
    dependencies=[Depends(require_admin())],
)
@limiter.limit("10/minute")
async def update_category(
    request: Request,
    category_id: UUID,
    category_data: CategoryUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Update a category's details by its ID."""
    try:
        category = await category_service.update_category(
            session, category_id, category_data
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return StandardResponse(
            success=True,
            message="Category updated successfully",
            data=category
        )
    except Exception as e:
        logger.error("Failed to update category", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category",
        )

@router.delete(
    "/{category_id}",
    response_model=StandardResponse[bool],
    status_code=status.HTTP_200_OK,
    summary="Delete a category",
    description="Delete a category. Requires admin privileges.",
    dependencies=[Depends(require_admin())],
)
@limiter.limit("5/minute")
async def delete_category(
    request: Request,
    category_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    """Permanently delete a category by its ID."""
    success = await category_service.delete_category(session, category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or could not be deleted",
        )
    return StandardResponse(
        success=True,
        message="Category deleted successfully",
        data=True
    ) 