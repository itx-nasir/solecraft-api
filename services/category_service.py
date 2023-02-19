"""
Service layer for category-related business logic.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import structlog

from models.orm.product import Category
from models.schemas.product import CategoryCreate, CategoryUpdate

logger = structlog.get_logger(__name__)


class CategoryService:
    """Service for category operations."""

    async def get_all_categories(
        self, session: AsyncSession
    ) -> List[Category]:
        """Retrieve all categories with their children."""
        try:
            result = await session.execute(
                select(Category)
                .options(selectinload(Category.children))
                .where(Category.parent_id.is_(None))  # Start from top-level
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                "Error retrieving all categories",
                error=str(e),
                exc_info=True
            )
            raise

    async def get_category_by_id(
        self, session: AsyncSession, category_id: UUID
    ) -> Optional[Category]:
        """Retrieve a single category by its ID."""
        try:
            result = await session.get(Category, category_id)
            return result
        except Exception as e:
            logger.error(
                "Error retrieving category by ID",
                category_id=category_id,
                error=str(e),
                exc_info=True
            )
            raise

    async def create_category(
        self, session: AsyncSession, category_data: CategoryCreate
    ) -> Category:
        """Create a new category."""
        try:
            new_category = Category(**category_data.model_dump())
            session.add(new_category)
            await session.flush()
            await session.refresh(new_category)
            logger.info("Category created successfully", category_id=new_category.id)
            return new_category
        except Exception as e:
            logger.error(
                "Error creating category",
                category_data=category_data.model_dump(),
                error=str(e),
                exc_info=True
            )
            raise

    async def update_category(
        self,
        session: AsyncSession,
        category_id: UUID,
        category_data: CategoryUpdate,
    ) -> Optional[Category]:
        """Update an existing category."""
        try:
            category = await self.get_category_by_id(session, category_id)
            if not category:
                return None

            update_data = category_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(category, key, value)
            
            await session.flush()
            await session.refresh(category)
            logger.info("Category updated successfully", category_id=category.id)
            return category
        except Exception as e:
            logger.error(
                "Error updating category",
                category_id=category_id,
                update_data=category_data.model_dump(exclude_unset=True),
                error=str(e),
                exc_info=True,
            )
            raise

    async def delete_category(
        self, session: AsyncSession, category_id: UUID
    ) -> bool:
        """Delete a category."""
        try:
            category = await self.get_category_by_id(session, category_id)
            if not category:
                return False
            
            await session.delete(category)
            await session.flush()
            logger.info("Category deleted successfully", category_id=category_id)
            return True
        except Exception as e:
            logger.error(
                "Error deleting category",
                category_id=category_id,
                error=str(e),
                exc_info=True
            )
            raise

category_service = CategoryService() 