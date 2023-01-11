"""
Abstract repository interfaces following the Repository pattern.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from models.orm import (
    User, Address, Category, Product, ProductVariant, ProductCustomization,
    Cart, CartItem, Order, OrderItem, Review, DiscountCode
)
from models.schemas import PaginationParams


class BaseRepository(ABC):
    """Base repository interface."""
    
    @abstractmethod
    async def create(self, **kwargs) -> Any:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def update(self, entity_id: UUID, **kwargs) -> Optional[Any]:
        """Update entity by ID."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID."""
        pass
    
    @abstractmethod
    async def list(
        self, 
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Any], int]:
        """List entities with pagination and filters."""
        pass


class IUserRepository(BaseRepository):
    """User repository interface."""
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass
    
    @abstractmethod
    async def get_by_session_id(self, session_id: str) -> Optional[User]:
        """Get user by session ID."""
        pass
    
    @abstractmethod
    async def create_guest_user(self, session_id: str, **kwargs) -> User:
        """Create a guest user."""
        pass
    
    @abstractmethod
    async def verify_user(self, user_id: UUID) -> bool:
        """Verify user account."""
        pass


class IProductRepository(BaseRepository):
    """Product repository interface."""
    
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Product]:
        """Get product by slug."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        category_id: Optional[UUID] = None,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Product], int]:
        """Search products with filters."""
        pass
    
    @abstractmethod
    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products."""
        pass


class ICartRepository(BaseRepository):
    """Cart repository interface."""
    
    @abstractmethod
    async def get_user_cart(self, user_id: UUID) -> Optional[Cart]:
        """Get user's cart."""
        pass
    
    @abstractmethod
    async def add_item(self, cart_id: UUID, **kwargs) -> CartItem:
        """Add item to cart."""
        pass
    
    @abstractmethod
    async def remove_item(self, cart_id: UUID, item_id: UUID) -> bool:
        """Remove item from cart."""
        pass


class IOrderRepository(BaseRepository):
    """Order repository interface."""
    
    @abstractmethod
    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number."""
        pass
    
    @abstractmethod
    async def get_user_orders(
        self, 
        user_id: UUID, 
        pagination: PaginationParams
    ) -> tuple[List[Order], int]:
        """Get user's orders."""
        pass 