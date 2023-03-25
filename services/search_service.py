"""
Service layer for search-related business logic.
"""
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_

from models.orm.product import Product
from models.schemas.product import ProductSearchRequest
from models.schemas.common import PaginationParams


class SearchService:
    """Service for search operations."""

    async def search_products(
        self,
        session: AsyncSession,
        search_params: ProductSearchRequest,
        pagination: PaginationParams,
    ) -> Tuple[List[Product], int]:
        """Search for products based on various criteria."""
        query = select(Product)
        
        filters = []
        if search_params.query:
            search_text = f"%{search_params.query}%"
            filters.append(
                or_(
                    Product.name.ilike(search_text),
                    Product.description.ilike(search_text),
                    Product.short_description.ilike(search_text)
                )
            )
        
        if search_params.min_price is not None:
            filters.append(Product.base_price >= search_params.min_price)
        if search_params.max_price is not None:
            filters.append(Product.base_price <= search_params.max_price)
        if search_params.is_featured is not None:
            filters.append(Product.is_featured == search_params.is_featured)
        if search_params.is_customizable is not None:
            filters.append(Product.is_customizable == search_params.is_customizable)
            
        # Remove commented code and logic for ProductVariant, color, size, etc.

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(Product).where(and_(*filters))
        total_result = await session.execute(count_query)
        total = len(total_result.scalars().all())

        # Apply pagination and sorting
        query = query.offset(pagination.offset).limit(pagination.page_size)
        
        result = await session.execute(query)
        products = list(result.scalars().all())
        
        return products, total

search_service = SearchService() 