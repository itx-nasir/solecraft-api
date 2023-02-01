"""
Product repository implementation.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
import structlog

from interfaces.repositories import IProductRepository
from models.orm import Product, Category, ProductVariant, ProductCustomization
from models.schemas import PaginationParams

logger = structlog.get_logger(__name__)


class ProductRepository(IProductRepository):
    """Product repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Product:
        """Create a new product."""
        product = Product(**kwargs)
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        logger.info("Product created", product_id=product.id, name=product.name)
        return product

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
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
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        """Get product by slug."""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.variants),
                selectinload(Product.customizations),
                selectinload(Product.reviews),
            )
            .where(Product.slug == slug)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, product_id: UUID, **kwargs) -> Optional[Product]:
        """Update product by ID."""
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(**kwargs)
            .returning(Product)
        )
        result = await self.session.execute(stmt)
        product = result.scalar_one_or_none()

        if product:
            await self.session.refresh(product)
            logger.info("Product updated", product_id=product.id)

        return product

    async def delete(self, product_id: UUID) -> bool:
        """Delete product by ID."""
        stmt = delete(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        success = result.rowcount > 0

        if success:
            logger.info("Product deleted", product_id=product_id)

        return success

    async def list(
        self,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Product], int]:
        """List products with pagination and filters."""
        base_stmt = select(Product)
        count_stmt = select(func.count(Product.id))

        if filters:
            conditions = self._apply_filters(filters)
            if conditions:
                base_stmt = base_stmt.where(*conditions)
                count_stmt = count_stmt.where(*conditions)

        # Get total count
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        stmt = (
            base_stmt
            .options(selectinload(Product.images)) # Only load images for list view for performance
            .offset(pagination.offset)
            .limit(pagination.page_size)
            .order_by(Product.created_at.desc())
        )

        result = await self.session.execute(stmt)
        products = result.scalars().all()

        return list(products), total

    async def search(
        self,
        query: Optional[str] = None,
        category_id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Product], int]:
        """Search products with filters."""
        base_stmt = select(Product)
        count_stmt = select(func.count(Product.id))

        conditions = []
        if query:
            search_query = f"%{query}%"
            conditions.append(
                (Product.name.ilike(search_query)) |
                (Product.description.ilike(search_query)) |
                (Product.short_description.ilike(search_query))
            )

        if category_id:
            conditions.append(Product.category_id == category_id)

        if filters:
            filter_conditions = self._apply_filters(filters)
            conditions.extend(filter_conditions)

        if conditions:
            base_stmt = base_stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)
        
        # Get total count
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        if pagination:
             stmt = (
                base_stmt
                .options(selectinload(Product.images))
                .offset(pagination.offset)
                .limit(pagination.page_size)
                .order_by(Product.created_at.desc())
            )
        else:
             stmt = (
                base_stmt
                .options(selectinload(Product.images))
                .order_by(Product.created_at.desc())
            )

        result = await self.session.execute(stmt)
        products = result.scalars().all()

        return list(products), total

    def _apply_filters(self, filters: Dict[str, Any]) -> list:
        """Helper to apply filter conditions."""
        conditions = []
        if filters.get("is_active") is not None:
            conditions.append(Product.is_active == filters["is_active"])
        if filters.get("is_featured") is not None:
            conditions.append(Product.is_featured == filters["is_featured"])
        if filters.get("is_customizable") is not None:
            conditions.append(Product.is_customizable == filters["is_customizable"])
        if filters.get("min_price"):
            conditions.append(Product.base_price >= filters["min_price"])
        if filters.get("max_price"):
            conditions.append(Product.base_price <= filters["max_price"])
        
        return conditions

    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products."""
        stmt = (
            select(Product)
            .where(Product.is_featured == True, Product.is_active == True)
            .limit(limit)
            .order_by(Product.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()) 