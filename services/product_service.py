"""
Product service containing business logic.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from slugify import slugify
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.product_repository import ProductRepository
from models.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    PaginationParams
)
from models.orm import Product

logger = structlog.get_logger(__name__)


class ProductService:
    """Product service for business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repo = ProductRepository(session)

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """Create a new product."""
        product_dict = product_data.model_dump()
        
        # Auto-generate slug if not provided
        if not product_data.slug:
            product_dict["slug"] = slugify(product_data.name)
        
        # Check if slug is unique
        existing_product = await self.product_repo.get_by_slug(product_dict["slug"])
        if existing_product:
            raise ValueError(f"Product with slug '{product_dict['slug']}' already exists.")

        product = await self.product_repo.create(**product_dict)
        await self.session.commit()
        await self.session.refresh(product, attribute_names=["category"])

        logger.info("Product created", product_id=product.id)
        
        return ProductResponse.model_validate(product)

    async def get_product_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        """Get product by ID."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            return None
        return ProductResponse.model_validate(product)

    async def get_product_by_slug(self, slug: str) -> Optional[ProductResponse]:
        """Get product by slug."""
        product = await self.product_repo.get_by_slug(slug)
        if not product:
            return None
        return ProductResponse.model_validate(product)

    async def update_product(
        self, product_id: UUID, product_data: ProductUpdate
    ) -> Optional[ProductResponse]:
        """Update a product."""
        update_data = product_data.model_dump(exclude_unset=True)

        # Handle slug update
        if "slug" in update_data:
            existing_product = await self.product_repo.get_by_slug(update_data["slug"])
            if existing_product and existing_product.id != product_id:
                raise ValueError(f"Product with slug '{update_data['slug']}' already exists.")
        elif "name" in update_data and "slug" not in update_data:
            # If name is updated but slug is not, regenerate slug
            update_data["slug"] = slugify(update_data["name"])

        updated_product = await self.product_repo.update(product_id, **update_data)
        if not updated_product:
            return None
            
        await self.session.commit()
        await self.session.refresh(updated_product, attribute_names=["category", "variants", "customizations"])
        
        logger.info("Product updated", product_id=updated_product.id)
        
        return ProductResponse.model_validate(updated_product)

    async def delete_product(self, product_id: UUID) -> bool:
        """Delete a product."""
        success = await self.product_repo.delete(product_id)
        if success:
            await self.session.commit()
            logger.info("Product deleted", product_id=product_id)
        return success

    async def list_products(
        self,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[ProductListResponse], int]:
        """List products with pagination and filters."""
        products, total = await self.product_repo.list(pagination, filters)
        
        # Eager load categories for all products in the list
        for p in products:
            await self.session.refresh(p, attribute_names=["category"])

        product_responses = [ProductListResponse.model_validate(p) for p in products]
        return product_responses, total
        
    async def search_products(
        self,
        query: Optional[str],
        category_id: Optional[UUID],
        filters: Optional[Dict[str, Any]],
        pagination: PaginationParams,
    ) -> Tuple[List[ProductListResponse], int]:
        """Search for products."""
        products, total = await self.product_repo.search(
            query=query,
            category_id=category_id,
            filters=filters,
            pagination=pagination
        )
        
        for p in products:
            await self.session.refresh(p, attribute_names=["category"])
            
        product_responses = [ProductListResponse.model_validate(p) for p in products]
        return product_responses, total

    async def get_featured_products(self, limit: int = 10) -> List[ProductListResponse]:
        """Get featured products."""
        products = await self.product_repo.get_featured_products(limit)

        for p in products:
            await self.session.refresh(p, attribute_names=["category"])

        product_responses = [ProductListResponse.model_validate(p) for p in products]
        return product_responses 