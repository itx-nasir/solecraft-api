"""
User repository implementation.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
import structlog

from interfaces.repositories import IUserRepository
from models.orm import User, Address
from models.schemas import PaginationParams

logger = structlog.get_logger(__name__)


class UserRepository(IUserRepository):
    """User repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, **kwargs) -> User:
        """Create a new user."""
        user = User(**kwargs)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        logger.info(f"User created", user_id=user.id, is_guest=user.is_guest)
        return user
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        stmt = (
            select(User)
            .options(selectinload(User.addresses))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_session_id(self, session_id: str) -> Optional[User]:
        """Get user by session ID."""
        stmt = select(User).where(User.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_guest_user(self, session_id: str, **kwargs) -> User:
        """Create a guest user."""
        user_data = {
            "is_guest": True,
            "session_id": session_id,
            "is_active": True,
            **kwargs
        }
        return await self.create(**user_data)
    
    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update user by ID."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**kwargs)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            await self.session.refresh(user)
            logger.info(f"User updated", user_id=user.id)
        
        return user
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        success = result.rowcount > 0
        
        if success:
            logger.info(f"User deleted", user_id=user_id)
        
        return success
    
    async def list(
        self,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[User], int]:
        """List users with pagination and filters."""
        base_stmt = select(User)
        count_stmt = select(func.count(User.id))
        
        # Apply filters
        if filters:
            conditions = []
            
            if filters.get("is_guest") is not None:
                conditions.append(User.is_guest == filters["is_guest"])
            
            if filters.get("is_active") is not None:
                conditions.append(User.is_active == filters["is_active"])
            
            if filters.get("email"):
                conditions.append(User.email.ilike(f"%{filters['email']}%"))
            
            if conditions:
                base_stmt = base_stmt.where(*conditions)
                count_stmt = count_stmt.where(*conditions)
        
        # Get total count
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()
        
        # Apply pagination
        stmt = (
            base_stmt
            .options(selectinload(User.addresses))
            .offset(pagination.offset)
            .limit(pagination.page_size)
            .order_by(User.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        return list(users), total
    
    async def verify_user(self, user_id: UUID) -> bool:
        """Verify user account."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True)
        )
        result = await self.session.execute(stmt)
        success = result.rowcount > 0
        
        if success:
            logger.info(f"User verified", user_id=user_id)
        
        return success


class AddressRepository:
    """Address repository implementation."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, **kwargs) -> Address:
        """Create a new address."""
        address = Address(**kwargs)
        self.session.add(address)
        await self.session.flush()
        await self.session.refresh(address)
        logger.info(f"Address created", address_id=address.id, user_id=address.user_id)
        return address
    
    async def get_by_id(self, address_id: UUID) -> Optional[Address]:
        """Get address by ID."""
        stmt = select(Address).where(Address.id == address_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_addresses(self, user_id: UUID) -> List[Address]:
        """Get all addresses for a user."""
        stmt = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_default_address(self, user_id: UUID) -> Optional[Address]:
        """Get user's default address."""
        stmt = (
            select(Address)
            .where(Address.user_id == user_id, Address.is_default == True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def set_default_address(self, user_id: UUID, address_id: UUID) -> bool:
        """Set address as default for user."""
        # First, unset all default addresses for the user
        await self.session.execute(
            update(Address)
            .where(Address.user_id == user_id)
            .values(is_default=False)
        )
        
        # Then set the specified address as default
        stmt = (
            update(Address)
            .where(Address.id == address_id, Address.user_id == user_id)
            .values(is_default=True)
        )
        result = await self.session.execute(stmt)
        success = result.rowcount > 0
        
        if success:
            logger.info(f"Default address set", user_id=user_id, address_id=address_id)
        
        return success
    
    async def update(self, address_id: UUID, **kwargs) -> Optional[Address]:
        """Update address by ID."""
        stmt = (
            update(Address)
            .where(Address.id == address_id)
            .values(**kwargs)
            .returning(Address)
        )
        result = await self.session.execute(stmt)
        address = result.scalar_one_or_none()
        
        if address:
            await self.session.refresh(address)
            logger.info(f"Address updated", address_id=address.id)
        
        return address
    
    async def delete(self, address_id: UUID) -> bool:
        """Delete address by ID."""
        stmt = delete(Address).where(Address.id == address_id)
        result = await self.session.execute(stmt)
        success = result.rowcount > 0
        
        if success:
            logger.info(f"Address deleted", address_id=address_id)
        
        return success 