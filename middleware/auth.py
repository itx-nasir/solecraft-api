"""
JWT Authentication middleware.
"""

from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.security import verify_token
from services.user_service import UserService
from models.orm import User

logger = structlog.get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current authenticated user."""
    token_data = verify_token(credentials.credentials)
    
    user_service = UserService(session)
    user = await user_service.get_by_id(token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (registered users only)."""
    if current_user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for guest users"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None
    
    try:
        token_data = verify_token(credentials.credentials)
        user_service = UserService(session)
        user = await user_service.get_by_id(token_data.user_id)
        
        if user and user.is_active:
            return user
    except HTTPException:
        pass
    
    return None


def require_admin():
    """
    Dependency to check if the user is an administrator.
    """
    async def admin_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.is_admin:
            logger.warning(
                "Admin access required",
                user_id=current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access required"
            )
        return current_user
    return admin_checker 