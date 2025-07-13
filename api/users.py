"""
User profile API routes.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from services.user_service import UserService
from middleware.auth import get_current_user, get_current_active_user
from models.schemas import (
    UserResponse, UserUpdate, AddressCreate, AddressUpdate, AddressResponse,
    StandardResponse
)
from models.orm import User
from middleware.rate_limit import limiter
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/profile",
    response_model=StandardResponse[UserResponse],
    summary="Get user profile",
    description="Get current user's profile information"
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get current user profile.
    """
    try:
        user_service = UserService(session)
        user_profile = await user_service.get_user_profile(current_user.id)
        return StandardResponse(
            success=True,
            message="Profile retrieved successfully",
            data=user_profile
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Get profile error", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve profile")


@router.put(
    "/profile",
    response_model=StandardResponse[UserResponse],
    summary="Update user profile",
    description="Update current user's profile information"
)
@limiter.limit("10/minute")
async def update_profile(
    request: Request,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update user profile.
    """
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Profile update error", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")


@router.get(
    "/addresses",
    response_model=StandardResponse[List[AddressResponse]],
    summary="Get user addresses",
    description="Get all addresses for the current user"
)
async def get_addresses(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all user addresses.
    
    Returns list of all saved addresses for the user.
    """
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve addresses")


@router.post(
    "/addresses",
    response_model=StandardResponse[AddressResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add new address",
    description="Add a new address to user's address book"
)
@limiter.limit("20/minute")
async def add_address(
    request: Request,
    address_data: AddressCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Add new address.
    """
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add address")


@router.put(
    "/addresses/{address_id}",
    response_model=StandardResponse[AddressResponse],
    summary="Update address",
    description="Update an existing address"
)
@limiter.limit("20/minute")
async def update_address(
    request: Request,
    address_id: UUID,
    address_data: AddressUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update address.
    
    Updates the specified address with new information.
    Only the address owner can update their addresses.
    """
    try:
        user_service = UserService(session)
        updated_address = await user_service.update_user_address(current_user.id, address_id, address_data)
        return StandardResponse(
            success=True,
            message="Address updated successfully",
            data=updated_address
        )
    except ValueError as e:
        logger.warning("Address update failed", error=str(e), user_id=current_user.id, address_id=address_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Address update error", error=str(e), user_id=current_user.id, address_id=address_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update address")


@router.delete(
    "/addresses/{address_id}",
    response_model=StandardResponse[bool],
    summary="Delete address",
    description="Delete an address from user's address book"
)
@limiter.limit("20/minute")
async def delete_address(
    request: Request,
    address_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete address.
    
    Permanently removes the specified address from user's address book.
    Only the address owner can delete their addresses.
    """
    try:
        user_service = UserService(session)
        success = await user_service.delete_user_address(current_user.id, address_id)
        return StandardResponse(
            success=True,
            message="Address deleted successfully",
            data=success
        )
    except Exception as e:
        logger.error("Delete address error", error=str(e), user_id=current_user.id, address_id=address_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete address") 