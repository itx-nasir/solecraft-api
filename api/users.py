"""
User profile API routes.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_async_session
from controllers.user_controller import UserController
from middleware.auth import get_current_user, get_current_active_user
from models.schemas import (
    UserResponse, UserUpdate, AddressCreate, AddressUpdate, AddressResponse,
    StandardResponse
)
from models.orm import User
from middleware.rate_limit import limiter

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
    
    Returns user information including:
    - Basic profile data
    - Account status
    - Registration details
    """
    return await UserController.get_profile(current_user, session)


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
    
    - **email**: New email address (optional)
    - **first_name**: First name (optional)
    - **last_name**: Last name (optional)
    - **username**: Username (optional)
    - **phone**: Phone number (optional)
    
    Note: Email changes may require verification.
    """
    return await UserController.update_profile(user_data, current_user, session)


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
    return await UserController.get_addresses(current_user, session)


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
    
    - **street_address**: Street address (required)
    - **city**: City (required)
    - **state**: State/Province (required)
    - **postal_code**: ZIP/Postal code (required)
    - **country**: Country (required)
    - **address_type**: Type of address (home, work, etc.)
    - **is_default**: Set as default address
    """
    return await UserController.add_address(address_data, current_user, session)


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
    return await UserController.update_address(address_id, address_data, current_user, session)


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
    return await UserController.delete_address(address_id, current_user, session) 