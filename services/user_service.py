"""
User service containing business logic.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import secrets
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user_repository import UserRepository, AddressRepository
from middleware.auth import get_password_hash, verify_password, create_access_token
from models.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserRegister,
    GuestUserCreate, AddressCreate, AddressUpdate, AddressResponse,
    TokenResponse, PaginationParams
)
from models.orm import User, Address
from workers.email_tasks import send_welcome_email, send_verification_email

logger = structlog.get_logger(__name__)


class UserService:
    """User service for business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.address_repo = AddressRepository(session)
    
    async def register_user(self, user_data: UserRegister) -> TokenResponse:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Check username if provided
        if user_data.username:
            existing_username = await self.user_repo.get_by_username(user_data.username)
            if existing_username:
                raise ValueError("Username already taken")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["password_hash"] = hashed_password
        user_dict["is_guest"] = False
        user_dict["is_active"] = True
        user_dict["is_verified"] = False
        
        user = await self.user_repo.create(**user_dict)
        await self.session.commit()
        
        logger.info("User registered", user_id=user.id, email=user.email)
        
        # Send welcome email (async task)
        send_welcome_email.delay(str(user.id), user.email, user.first_name or "User")
        
        # Generate verification token and send email
        verification_token = self._generate_verification_token(user.id)
        send_verification_email.delay(str(user.id), user.email, verification_token)
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "is_guest": False
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": str(user.id),
                "email": user.email,
                "is_guest": False,
                "is_verified": user.is_verified
            }
        )
    
    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        """Authenticate user and return token."""
        user = await self.user_repo.get_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        # Update last login
        await self.user_repo.update(user.id, last_login=datetime.utcnow())
        await self.session.commit()
        
        logger.info("User logged in", user_id=user.id, email=user.email)
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "is_guest": user.is_guest
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": str(user.id),
                "email": user.email,
                "is_guest": user.is_guest,
                "is_verified": user.is_verified
            }
        )
    
    async def create_guest_user(self, guest_data: GuestUserCreate) -> TokenResponse:
        """Create a guest user."""
        # Check if guest user already exists with this session
        existing_guest = await self.user_repo.get_by_session_id(guest_data.session_id)
        if existing_guest:
            # Return existing guest user token
            access_token = create_access_token(
                data={
                    "sub": str(existing_guest.id),
                    "email": existing_guest.email,
                    "is_guest": True,
                    "session_id": existing_guest.session_id
                }
            )
            
            return TokenResponse(
                access_token=access_token,
                expires_in=24 * 60 * 60,  # 24 hours for guests
                user={
                    "id": str(existing_guest.id),
                    "session_id": existing_guest.session_id,
                    "is_guest": True
                }
            )
        
        # Create new guest user
        guest_dict = guest_data.model_dump()
        guest_dict["is_guest"] = True
        guest_dict["is_active"] = True
        
        user = await self.user_repo.create(**guest_dict)
        await self.session.commit()
        
        logger.info("Guest user created", user_id=user.id, session_id=user.session_id)
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "is_guest": True,
                "session_id": user.session_id
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            expires_in=24 * 60 * 60,  # 24 hours for guests
            user={
                "id": str(user.id),
                "session_id": user.session_id,
                "is_guest": True
            }
        )
    
    async def get_user_profile(self, user_id: UUID) -> UserResponse:
        """Get user profile."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        return UserResponse.model_validate(user)
    
    async def update_user_profile(self, user_id: UUID, user_data: UserUpdate) -> UserResponse:
        """Update user profile."""
        # Check if email is being updated and is available
        if user_data.email:
            existing_user = await self.user_repo.get_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already in use")
        
        # Check if username is being updated and is available
        if user_data.username:
            existing_username = await self.user_repo.get_by_username(user_data.username)
            if existing_username and existing_username.id != user_id:
                raise ValueError("Username already taken")
        
        # Update user
        updated_user = await self.user_repo.update(
            user_id, 
            **user_data.model_dump(exclude_unset=True)
        )
        
        if not updated_user:
            raise ValueError("User not found")
        
        await self.session.commit()
        
        logger.info("User profile updated", user_id=user_id)
        
        return UserResponse.model_validate(updated_user)
    
    async def add_user_address(self, user_id: UUID, address_data: AddressCreate) -> AddressResponse:
        """Add address to user."""
        address_dict = address_data.model_dump()
        address_dict["user_id"] = user_id
        
        # If this is set as default, unset other defaults
        if address_data.is_default:
            await self.address_repo.set_default_address(user_id, None)  # Unset all defaults first
        
        address = await self.address_repo.create(**address_dict)
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
        # Verify address belongs to user
        address = await self.address_repo.get_by_id(address_id)
        if not address or address.user_id != user_id:
            raise ValueError("Address not found")
        
        # If setting as default, unset other defaults
        if address_data.is_default:
            await self.address_repo.set_default_address(user_id, address_id)
        
        updated_address = await self.address_repo.update(
            address_id,
            **address_data.model_dump(exclude_unset=True)
        )
        
        await self.session.commit()
        
        logger.info("Address updated", user_id=user_id, address_id=address_id)
        
        return AddressResponse.model_validate(updated_address)
    
    async def delete_user_address(self, user_id: UUID, address_id: UUID) -> bool:
        """Delete user address."""
        # Verify address belongs to user
        address = await self.address_repo.get_by_id(address_id)
        if not address or address.user_id != user_id:
            raise ValueError("Address not found")
        
        success = await self.address_repo.delete(address_id)
        await self.session.commit()
        
        if success:
            logger.info("Address deleted", user_id=user_id, address_id=address_id)
        
        return success
    
    async def get_user_addresses(self, user_id: UUID) -> List[AddressResponse]:
        """Get all user addresses."""
        addresses = await self.address_repo.get_user_addresses(user_id)
        return [AddressResponse.model_validate(addr) for addr in addresses]
    
    def _generate_verification_token(self, user_id: UUID) -> str:
        """Generate verification token for email verification."""
        token = secrets.token_urlsafe(32)
        # Store token in Redis with 24 hour expiration
        from core.config import settings
        import redis
        
        redis_client = redis.Redis.from_url(settings.redis_url)
        redis_client.setex(
            f"verification_token:{token}", 
            86400,  # 24 hours
            str(user_id)
        )
        
        return token
    
    async def verify_email_token(self, token: str) -> bool:
        """Verify email verification token."""
        from core.config import settings
        import redis
        
        try:
            redis_client = redis.Redis.from_url(settings.redis_url)
            user_id_str = redis_client.get(f"verification_token:{token}")
            
            if not user_id_str:
                raise ValueError("Invalid or expired verification token")
            
            user_id = UUID(user_id_str.decode())
            
            # Update user as verified
            await self.user_repo.update(user_id, is_verified=True)
            await self.session.commit()
            
            # Delete the token
            redis_client.delete(f"verification_token:{token}")
            
            logger.info("Email verified successfully", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Email verification failed", error=str(e), token=token)
            raise ValueError("Invalid or expired verification token")
    
    async def resend_verification_email(self, email: str) -> bool:
        """Resend verification email."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        
        if user.is_verified:
            raise ValueError("Email already verified")
        
        # Generate new verification token
        verification_token = self._generate_verification_token(user.id)
        send_verification_email.delay(str(user.id), user.email, verification_token)
        
        logger.info("Verification email resent", user_id=user.id, email=user.email)
        return True 