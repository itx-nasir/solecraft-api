"""
Product service containing business logic.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from slugify import slugify
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

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

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """Create a new product."""
        product_dict = product_data.model_dump()
        
        if not product_data.slug:
            product_dict["slug"] = slugify(product_data.name)
        
        existing_product = await self.get_product_by_slug(product_dict["slug"])
        if existing_product:
            raise ValueError(f"Product with slug '{product_dict['slug']}' already exists.")

        product = Product(**product_dict)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)

        logger.info("Product created", product_id=product.id)
        
        return ProductResponse.model_validate(product)

    async def get_product_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        """Get product by ID."""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.customizations),
                selectinload(Product.reviews),
            )
            .where(Product.id == product_id)
        )
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            return None
        return ProductResponse.model_validate(product)

    async def get_product_by_slug(self, slug: str) -> Optional[ProductResponse]:
        """Get product by slug."""
        stmt = select(Product).where(Product.slug == slug)
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            return None
        return ProductResponse.model_validate(product)

    async def update_product(
        self, product_id: UUID, product_data: ProductUpdate
    ) -> Optional[ProductResponse]:
        """Update a product."""
        update_data = product_data.model_dump(exclude_unset=True)

        if "slug" in update_data:
            existing_product_slug = await self.get_product_by_slug(update_data["slug"])
            if existing_product_slug and existing_product_slug.id != product_id:
                raise ValueError(f"Product with slug '{update_data['slug']}' already exists.")
        elif "name" in update_data and "slug" not in update_data:
            update_data["slug"] = slugify(update_data["name"])

        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(**update_data)
            .returning(Product)
        )
        result = await self.session.execute(stmt)
        updated_product = result.scalar_one_or_none()
        
        if not updated_product:
            return None
            
        await self.session.commit()
        await self.session.refresh(updated_product)
        
        logger.info("Product updated", product_id=updated_product.id)
        
        return ProductResponse.model_validate(updated_product)

    async def delete_product(self, product_id: UUID) -> bool:
        """Delete a product."""
        stmt = delete(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        success = result.rowcount > 0
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
        base_stmt = select(Product)
        count_stmt = select(func.count(Product.id))

        if filters:
            conditions = self._apply_filters(filters)
            if conditions:
                base_stmt = base_stmt.where(*conditions)
                count_stmt = count_stmt.where(*conditions)

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            base_stmt
            .offset(pagination.offset)
            .limit(pagination.page_size)
            .order_by(Product.created_at.desc())
        )

        result = await self.session.execute(stmt)
        products = result.scalars().all()
        product_responses = [ProductListResponse.model_validate(p) for p in products]
        return product_responses, total

    def _apply_filters(self, filters: Dict[str, Any]) -> list:
        """Helper to apply filter conditions."""
        conditions = []
        if "category_id" in filters and filters["category_id"] is not None:
            conditions.append(Product.category_id == filters["category_id"])
        if "is_featured" in filters and filters["is_featured"] is not None:
            conditions.append(Product.is_featured == filters["is_featured"])
        return conditions 