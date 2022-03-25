"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, status, Request, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from models.schemas import (
    UserRegister, UserLogin, GuestUserCreate, TokenResponse, StandardResponse,
    EmailVerificationRequest, ResendVerificationRequest
)
from services.user_service import UserService
from services import background_tasks_service
from core.security import create_access_token
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
async def register(
    request: Request,
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user.
    """
    try:
        user_service = UserService(session)
        user = await user_service.register_user(user_data)
        
        # Add email tasks to background
        verification_token = user_service.generate_verification_token(user.id, user.email)
        background_tasks.add_task(background_tasks_service.send_welcome_email, str(user.id), user.email, user.first_name or "User")
        background_tasks.add_task(background_tasks_service.send_verification_email, str(user.id), user.email, verification_token)

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "is_guest": False}
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": str(user.id),
                "email": user.email,
                "is_guest": False,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin
            }
        )

        return StandardResponse(
            success=True,
            message="User registered successfully",
            data=token_response
        )
        
    except ValueError as e:
        logger.warning("User registration failed", error=str(e), email=user_data.email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("User registration error", error=str(e), email=user_data.email)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    summary="User login",
    description="Authenticate user with email and password"
)
async def login(
    request: Request,
    login_data: UserLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Login user.
    """
    try:
        user_service = UserService(session)
        user = await user_service.login_user(login_data)

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "is_guest": user.is_guest}
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": str(user.id),
                "email": user.email,
                "is_guest": user.is_guest,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin
            }
        )
        
        return StandardResponse(
            success=True,
            message="Login successful",
            data=token_response
        )
        
    except ValueError as e:
        logger.warning("User login failed", error=str(e), email=login_data.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("User login error", error=str(e), email=login_data.email)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.post(
    "/guest",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create guest user",
    description="Create a guest user session for anonymous checkout"
)
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
    try:
        user_service = UserService(session)
        return await user_service.create_guest_user(guest_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Guest user creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


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


@router.get("/verify-email")
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Verify user email with token from query parameter."""
    try:
        user_service = UserService(session)
        await user_service.verify_email_token(token)
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/resend-verification")
async def resend_verification(
    request_data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """Resend verification email."""
    try:
        user_service = UserService(session)
        user = await user_service.resend_verification_email(request_data.email)
        verification_token = user_service.generate_verification_token(user.id, user.email)
        background_tasks.add_task(background_tasks_service.send_verification_email, str(user.id), user.email, verification_token)
        return {"message": "Verification email sent"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Resend verification failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test-email")
async def test_email(
    email: str,
    background_tasks: BackgroundTasks,
):
    """Test email functionality (development only)."""
    from core.config import settings
    
    if settings.environment != "development":
        raise HTTPException(status_code=403, detail="Test endpoint only available in development")
    
    try:
        background_tasks.add_task(background_tasks_service.send_welcome_email, "test-user-id", email, "Test User")
        return {"message": f"Test email sent to {email}"}
    except Exception as e:
        logger.error("Test email failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send test email") 