"""
Product API routes.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from services.product_service import ProductService
from middleware.auth import require_admin
from models.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    StandardResponse, PaginatedResponse, PaginationParams
)
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=StandardResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product. Requires admin access.",
    dependencies=[Depends(require_admin())]
)
async def create_product(
    request: Request,
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new product.
    """
    try:
        product_service = ProductService(session)
        product = await product_service.create_product(product_data)
        return StandardResponse(
            success=True, message="Product created successfully", data=product
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to create product", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create product")


@router.get(
    "",
    response_model=PaginatedResponse[ProductListResponse],
    summary="List products",
    description="Get a paginated list of products."
)
async def list_products(
    pagination: PaginationParams = Depends(),
    is_featured: Optional[bool] = Query(None, description="Filter by featured products"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve a list of products.
    """
    try:
        product_service = ProductService(session)
        filters = {"is_featured": is_featured}
        products, total = await product_service.list_products(pagination, filters)
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        return PaginatedResponse(
            items=products,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1
        )
    except Exception as e:
        logger.error("Failed to list products", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list products")


@router.get(
    "/{product_id}",
    response_model=StandardResponse[ProductResponse],
    summary="Get a single product",
    description="Get detailed information about a single product by its ID."
)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get a single product by its UUID.
    """
    product_service = ProductService(session)
    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return StandardResponse(success=True, message="Product found", data=product)


@router.put(
    "/{product_id}",
    response_model=StandardResponse[ProductResponse],
    summary="Update a product",
    description="Update an existing product's information. Requires admin access.",
    dependencies=[Depends(require_admin())]
)
async def update_product(
    request: Request,
    product_id: UUID,
    product_data: ProductUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update a product's details by its ID.
    """
    try:
        product_service = ProductService(session)
        product = await product_service.update_product(product_id, product_data)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return StandardResponse(success=True, message="Product updated successfully", data=product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Failed to update product", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update product")


@router.delete(
    "/{product_id}",
    response_model=StandardResponse[bool],
    status_code=status.HTTP_200_OK,
    summary="Delete a product",
    description="Delete a product. Requires admin access.",
    dependencies=[Depends(require_admin())]
)
async def delete_product(
    request: Request,
    product_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """

    Permanently delete a product by its ID.
    """
    product_service = ProductService(session)
    success = await product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or could not be deleted")
    return StandardResponse(success=True, message="Product deleted successfully", data=True) 