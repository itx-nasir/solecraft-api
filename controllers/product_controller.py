"""
Product controller handling HTTP requests.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from infrastructure.database import get_async_session
from services.product_service import ProductService
from middleware.auth import get_current_user, get_optional_current_user, require_permissions
from models.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    StandardResponse, PaginatedResponse, PaginationParams
)
from models.orm import User

logger = structlog.get_logger(__name__)


class ProductController:
    """Product controller for handling product-related requests."""

    @staticmethod
    async def create_product(
        product_data: ProductCreate,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(require_permissions("product:create"))
    ) -> StandardResponse[ProductResponse]:
        """Create a new product."""
        try:
            product_service = ProductService(session)
            product = await product_service.create_product(product_data)
            return StandardResponse(
                success=True,
                message="Product created successfully",
                data=product
            )
        except ValueError as e:
            logger.warning("Product creation failed", error=str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error("Product creation error", error=str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create product")

    @staticmethod
    async def get_product(
        product_id: UUID,
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[ProductResponse]:
        """Get a single product by ID."""
        product_service = ProductService(session)
        product = await product_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return StandardResponse(success=True, message="Product retrieved successfully", data=product)

    @staticmethod
    async def get_product_by_slug(
        slug: str,
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[ProductResponse]:
        """Get a single product by slug."""
        product_service = ProductService(session)
        product = await product_service.get_product_by_slug(slug)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return StandardResponse(success=True, message="Product retrieved successfully", data=product)

    @staticmethod
    async def list_products(
        pagination: PaginationParams = Depends(),
        category_id: Optional[UUID] = Query(None),
        is_featured: Optional[bool] = Query(None),
        session: AsyncSession = Depends(get_async_session)
    ) -> PaginatedResponse[ProductListResponse]:
        """List products with optional filters."""
        try:
            product_service = ProductService(session)
            filters = {"is_active": True}
            if category_id:
                filters["category_id"] = category_id
            if is_featured is not None:
                filters["is_featured"] = is_featured
            
            products, total = await product_service.list_products(pagination, filters)
            
            return PaginatedResponse(
                items=products,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=(total + pagination.page_size - 1) // pagination.page_size,
                has_next=((pagination.page * pagination.page_size) < total),
                has_prev=(pagination.page > 1)
            )
        except Exception as e:
            logger.error("Failed to list products", error=str(e))
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve products")

    @staticmethod
    async def update_product(
        product_id: UUID,
        product_data: ProductUpdate,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(require_permissions("product:update"))
    ) -> StandardResponse[ProductResponse]:
        """Update a product."""
        try:
            product_service = ProductService(session)
            updated_product = await product_service.update_product(product_id, product_data)
            if not updated_product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            return StandardResponse(success=True, message="Product updated successfully", data=updated_product)
        except ValueError as e:
            logger.warning("Product update failed", error=str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error("Product update error", error=str(e), product_id=product_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update product")

    @staticmethod
    async def delete_product(
        product_id: UUID,
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(require_permissions("product:delete"))
    ) -> StandardResponse[bool]:
        """Delete a product."""
        try:
            product_service = ProductService(session)
            success = await product_service.delete_product(product_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            return StandardResponse(success=True, message="Product deleted successfully", data=True)
        except Exception as e:
            logger.error("Product deletion error", error=str(e), product_id=product_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete product") 