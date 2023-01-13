"""
User controller handling HTTP requests.
"""

from typing import List
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from infrastructure.database import get_async_session
from services.user_service import UserService
from middleware.auth import get_current_user, get_current_active_user
from models.schemas import (
    UserResponse, UserUpdate, UserRegister, UserLogin, GuestUserCreate,
    AddressCreate, AddressUpdate, AddressResponse, TokenResponse,
    StandardResponse
)
from models.orm import User

logger = structlog.get_logger(__name__)


class UserController:
    """User controller for handling user-related requests."""
    
    @staticmethod
    async def register(
        user_data: UserRegister,
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[TokenResponse]:
        """Register a new user."""
        try:
            user_service = UserService(session)
            token_response = await user_service.register_user(user_data)
            
            return StandardResponse(
                success=True,
                message="User registered successfully",
                data=token_response
            )
            
        except ValueError as e:
            logger.warning("User registration failed", error=str(e), email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error("User registration error", error=str(e), email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    @staticmethod
    async def login(
        login_data: UserLogin,
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[TokenResponse]:
        """Login user and return token."""
        try:
            user_service = UserService(session)
            token_response = await user_service.login_user(login_data)
            
            return StandardResponse(
                success=True,
                message="Login successful",
                data=token_response
            )
            
        except ValueError as e:
            logger.warning("User login failed", error=str(e), email=login_data.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        except Exception as e:
            logger.error("User login error", error=str(e), email=login_data.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    @staticmethod
    async def create_guest(
        guest_data: GuestUserCreate,
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[TokenResponse]:
        """Create a guest user."""
        try:
            user_service = UserService(session)
            token_response = await user_service.create_guest_user(guest_data)
            
            return StandardResponse(
                success=True,
                message="Guest user created successfully",
                data=token_response
            )
            
        except Exception as e:
            logger.error("Guest user creation error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create guest user"
            )
    
    @staticmethod
    async def get_profile(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[UserResponse]:
        """Get current user profile."""
        try:
            user_service = UserService(session)
            user_profile = await user_service.get_user_profile(current_user.id)
            
            return StandardResponse(
                success=True,
                message="Profile retrieved successfully",
                data=user_profile
            )
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error("Get profile error", error=str(e), user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve profile"
            )
    
    @staticmethod
    async def update_profile(
        user_data: UserUpdate,
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[UserResponse]:
        """Update current user profile."""
        try:
            user_service = UserService(session)
            updated_user = await user_service.update_user_profile(current_user.id, user_data)
            
            return StandardResponse(
                success=True,
                message="Profile updated successfully",
                data=updated_user
            )
            
        except ValueError as e:
            logger.warning("Profile update failed", error=str(e), user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error("Profile update error", error=str(e), user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
    
    @staticmethod
    async def add_address(
        address_data: AddressCreate,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[AddressResponse]:
        """Add new address to user."""
        try:
            user_service = UserService(session)
            address = await user_service.add_user_address(current_user.id, address_data)
            
            return StandardResponse(
                success=True,
                message="Address added successfully",
                data=address
            )
            
        except Exception as e:
            logger.error("Add address error", error=str(e), user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add address"
            )
    
    @staticmethod
    async def update_address(
        address_id: UUID,
        address_data: AddressUpdate,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[AddressResponse]:
        """Update user address."""
        try:
            user_service = UserService(session)
            address = await user_service.update_user_address(
                current_user.id, address_id, address_data
            )
            
            return StandardResponse(
                success=True,
                message="Address updated successfully",
                data=address
            )
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error("Update address error", error=str(e), user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update address"
            )
    
    @staticmethod
    async def delete_address(
        address_id: UUID,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[bool]:
        """Delete user address."""
        try:
            user_service = UserService(session)
            success = await user_service.delete_user_address(current_user.id, address_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Address not found"
                )
            
            return StandardResponse(
                success=True,
                message="Address deleted successfully",
                data=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Delete address error", error=str(e), user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete address"
            )
    
    @staticmethod
    async def get_addresses(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> StandardResponse[List[AddressResponse]]:
        """Get all user addresses."""
        try:
            user_service = UserService(session)
            addresses = await user_service.get_user_addresses(current_user.id)
            
            return StandardResponse(
                success=True,
                message="Addresses retrieved successfully",
                data=addresses
            )
            
        except Exception as e:
            logger.error("Get addresses error", error=str(e), user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve addresses"
            ) 