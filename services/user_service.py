"""
User service containing business logic.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import secrets
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from core.security import get_password_hash, verify_password, create_access_token, verify_token
from models.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserRegister,
    GuestUserCreate, AddressCreate, AddressUpdate, AddressResponse,
    TokenResponse, PaginationParams
)
from models.orm import User, Address

logger = structlog.get_logger(__name__)


class UserService:
    """User service for business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def register_user(self, user_data: UserRegister) -> User:
        """Register a new user."""
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        if user_data.username:
            existing_username = await self.get_by_username(user_data.username)
            if existing_username:
                raise ValueError("Username already taken")
        
        hashed_password = get_password_hash(user_data.password)
        
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["password_hash"] = hashed_password
        user_dict["is_guest"] = False
        user_dict["is_active"] = True
        user_dict["is_verified"] = False
        
        user = User(**user_dict)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info("User registered", user_id=user.id, email=user.email)
        
        return user
    
    async def login_user(self, login_data: UserLogin) -> User:
        """Authenticate user and return user object."""
        user = await self.get_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        user.last_login = datetime.utcnow()
        await self.session.commit()
        
        logger.info("User logged in", user_id=user.id, email=user.email)
        
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).options(selectinload(User.addresses)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_user_profile(self, user_id: UUID) -> UserResponse:
        """Get user profile."""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        return UserResponse.model_validate(user)
    
    async def update_user_profile(self, user_id: UUID, user_data: UserUpdate) -> UserResponse:
        """Update user profile."""
        if user_data.email:
            existing_user = await self.get_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already in use")
        
        if user_data.username:
            existing_username = await self.get_by_username(user_data.username)
            if existing_username and existing_username.id != user_id:
                raise ValueError("Username already taken")
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**user_data.model_dump(exclude_unset=True))
            .returning(User)
        )
        result = await self.session.execute(stmt)
        updated_user = result.scalar_one_or_none()

        if not updated_user:
            raise ValueError("User not found")
        
        await self.session.commit()
        
        logger.info("User profile updated", user_id=user_id)
        
        return UserResponse.model_validate(updated_user)
    
    async def add_user_address(self, user_id: UUID, address_data: AddressCreate) -> AddressResponse:
        """Add address to user."""
        if address_data.is_default:
            await self.session.execute(
                update(Address).where(Address.user_id == user_id).values(is_default=False)
            )

        address = Address(**address_data.model_dump(), user_id=user_id)
        self.session.add(address)
        await self.session.commit()
        
        logger.info("Address added", user_id=user_id, address_id=address.id)
        
        return AddressResponse.model_validate(address)
    
    async def update_user_address(
        self, 
        user_id: UUID, 
        address_id: UUID, 
        address_data: AddressUpdate
    ) -> AddressResponse:
        """Update user address."""
        address = await self.get_address_by_id(address_id)
        if not address or address.user_id != user_id:
            raise ValueError("Address not found")
        
        if address_data.is_default:
            await self.session.execute(
                update(Address).where(Address.user_id == user_id).values(is_default=False)
            )
        
        update_stmt = (
            update(Address)
            .where(Address.id == address_id)
            .values(**address_data.model_dump(exclude_unset=True))
            .returning(Address)
        )
        result = await self.session.execute(update_stmt)
        updated_address = result.scalar_one_or_none()
        await self.session.commit()
        
        return AddressResponse.model_validate(updated_address)

    async def get_address_by_id(self, address_id: UUID) -> Optional[Address]:
        """Get an address by its ID."""
        result = await self.session.execute(select(Address).where(Address.id == address_id))
        return result.scalar_one_or_none()

    async def get_user_address_by_id(self, user_id: UUID, address_id: UUID) -> Optional[Address]:
        """Get a single address by its ID, scoped to a user."""
        result = await self.session.execute(
            select(Address).where(Address.id == address_id, Address.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_addresses(self, user_id: UUID) -> List[AddressResponse]:
        """Get all addresses for a user."""
        result = await self.session.execute(
            select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc())
        )
        addresses = result.scalars().all()
        return [AddressResponse.model_validate(addr) for addr in addresses]

    async def delete_user_address(self, user_id: UUID, address_id: UUID) -> bool:
        """Delete user address."""
        address = await self.get_address_by_id(address_id)
        if not address or address.user_id != user_id:
            raise ValueError("Address not found")
        
        stmt = delete(Address).where(Address.id == address_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    def generate_verification_token(self, user_id: UUID, email: str) -> str:
        """Generate a secure, short-lived JWT for email verification."""
        expires_delta = timedelta(hours=1)
        token_data = {"sub": str(user_id), "scope": "email_verification"}
        token = create_access_token(token_data, expires_delta=expires_delta)
        return token

    async def verify_email_token(self, token: str) -> bool:
        """Verify the email verification token and update user status."""
        try:
            token_data = verify_token(token)
            if token_data.scope != "email_verification":
                raise ValueError("Invalid token scope")

            user = await self.get_by_id(UUID(token_data.user_id))

            if not user:
                raise ValueError("User not found")

            if user.is_verified:
                logger.info("Email already verified", user_id=user.id)
                return True

            user.is_verified = True
            await self.session.commit()
            logger.info("Email verified successfully", user_id=user.id)
            return True

        except Exception as e:
            logger.error("Email token verification failed", error=str(e))
            raise ValueError("Invalid or expired verification token")

    async def resend_verification_email(self, email: str) -> User:
        """Resend verification email."""
        user = await self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        if user.is_verified:
            raise ValueError("Email already verified")

        return user 