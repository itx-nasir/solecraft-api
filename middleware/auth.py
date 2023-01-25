"""
JWT Authentication middleware with RBAC.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.config import settings
from infrastructure.database import get_async_session
from repositories.user_repository import UserRepository
from models.schemas import TokenData
from models.orm import User, Role

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(
            user_id=user_id,
            email=payload.get("email"),
            is_guest=payload.get("is_guest", False),
            session_id=payload.get("session_id")
        )
        return token_data
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current authenticated user with roles and permissions."""
    token_data = verify_token(credentials.credentials)
    
    # Load user with roles and permissions
    stmt = (
        select(User)
        .options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
        .where(User.id == token_data.user_id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
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
        
        stmt = (
            select(User)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
            .where(User.id == token_data.user_id)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user and user.is_active:
            return user
    except HTTPException:
        pass
    
    return None


def require_permissions(*required_permissions: str):
    """
    Dependency to check for specific permissions.
    Can require multiple permissions (user must have ALL of them).
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not required_permissions:
            return current_user
        
        user_permissions = current_user.get_permissions()
        
        missing_permissions = []
        for permission in required_permissions:
            if permission not in user_permissions:
                missing_permissions.append(permission)
        
        if missing_permissions:
            logger.warning(
                "Permission denied",
                user_id=current_user.id,
                required_permissions=required_permissions,
                missing_permissions=missing_permissions,
                user_permissions=user_permissions
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing_permissions)}"
            )
        
        logger.debug(
            "Permission granted",
            user_id=current_user.id,
            permissions=required_permissions
        )
        return current_user
    
    return permission_checker


def require_any_permission(*required_permissions: str):
    """
    Dependency to check for any of the specified permissions.
    User must have AT LEAST ONE of the specified permissions.
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not required_permissions:
            return current_user
        
        user_permissions = current_user.get_permissions()
        
        has_any_permission = any(
            permission in user_permissions 
            for permission in required_permissions
        )
        
        if not has_any_permission:
            logger.warning(
                "Permission denied - no required permissions",
                user_id=current_user.id,
                required_permissions=required_permissions,
                user_permissions=user_permissions
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required_permissions)}"
            )
        
        logger.debug(
            "Permission granted",
            user_id=current_user.id,
            permissions=required_permissions
        )
        return current_user
    
    return permission_checker


def require_role(*required_roles: str):
    """
    Dependency to check for specific roles.
    User must have AT LEAST ONE of the specified roles.
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not required_roles:
            return current_user
        
        user_roles = [role.name for role in current_user.roles if role.is_active]
        
        has_required_role = any(
            role in user_roles 
            for role in required_roles
        )
        
        if not has_required_role:
            logger.warning(
                "Role access denied",
                user_id=current_user.id,
                required_roles=required_roles,
                user_roles=user_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(required_roles)}"
            )
        
        logger.debug(
            "Role access granted",
            user_id=current_user.id,
            roles=required_roles
        )
        return current_user
    
    return role_checker


def require_admin():
    """Dependency to check for admin access (admin or super_admin role)."""
    return require_role("admin", "super_admin")


def require_staff():
    """Dependency to check for staff access (any role)."""
    async def staff_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.is_staff or not current_user.roles:
            logger.warning(
                "Staff access denied",
                user_id=current_user.id,
                is_staff=current_user.is_staff,
                roles_count=len(current_user.roles)
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff access required"
            )
        
        return current_user
    
    return staff_checker


# Backward compatibility - keeping the old function name but using new system
def has_permission(permission: str):
    """
    Backward compatibility function.
    Use require_permissions() for new code.
    """
    return require_permissions(permission) 