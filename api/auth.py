"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_async_session
from controllers.user_controller import UserController
from models.schemas import (
    UserRegister, UserLogin, GuestUserCreate, TokenResponse, StandardResponse,
    EmailVerificationRequest, ResendVerificationRequest
)
from middleware.rate_limit import limiter
from services.user_service import UserService
from core.container import get_container
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post(
    "/register",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account with email and password"
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegister,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user.
    
    - **email**: Valid email address (required)
    - **password**: Strong password (required)
    - **first_name**: User's first name (optional)
    - **last_name**: User's last name (optional)
    - **username**: Unique username (optional)
    - **phone**: Phone number (optional)
    """
    return await UserController.register(user_data, session)


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    summary="User login",
    description="Authenticate user with email and password"
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Login user.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT access token for authenticated requests.
    """
    return await UserController.login(login_data, session)


@router.post(
    "/guest",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create guest user",
    description="Create a guest user session for anonymous checkout"
)
@limiter.limit("20/minute")
async def create_guest(
    request: Request,
    guest_data: GuestUserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create guest user.
    
    - **session_id**: Unique session identifier for guest user
    - **email**: Email address for order notifications (optional)
    
    Returns token for guest user that can be used for shopping and checkout.
    Guest sessions expire after 24 hours.
    """
    return await UserController.create_guest(guest_data, session)


@router.post("/guest-token", response_model=TokenResponse)
async def create_guest_token(
    guest_data: GuestUserCreate,
    session: AsyncSession = Depends(get_async_session)
) -> TokenResponse:
    """Create guest user token for checkout."""
    try:
        user_service = UserService(session)
        return await user_service.create_guest_user(guest_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Guest token creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify-email")
async def verify_email(
    request_data: EmailVerificationRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Verify user email with token."""
    try:
        user_service = UserService(session)
        await user_service.verify_email_token(request_data.token)
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/resend-verification")
async def resend_verification(
    request_data: ResendVerificationRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Resend verification email."""
    try:
        user_service = UserService(session)
        await user_service.resend_verification_email(request_data.email)
        return {"message": "Verification email sent"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Resend verification failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test-email")
async def test_email(
    email: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Test email functionality (development only)."""
    from core.config import settings
    
    if settings.environment != "development":
        raise HTTPException(status_code=403, detail="Test endpoint only available in development")
    
    try:
        from workers.email_tasks import send_welcome_email
        # Send a test welcome email
        send_welcome_email.delay("test-user-id", email, "Test User")
        return {"message": f"Test email sent to {email}"}
    except Exception as e:
        logger.error("Test email failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send test email") 