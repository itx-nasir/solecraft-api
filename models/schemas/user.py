"""
User domain Pydantic schemas.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
import uuid


class AddressBase(BaseModel):
    """Base address schema."""
    label: Optional[str] = Field(None, max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    street_address_1: str = Field(..., max_length=255)
    street_address_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(..., max_length=2, description="ISO 3166-1 alpha-2 country code")
    phone: Optional[str] = Field(None, max_length=20)
    is_default: bool = Field(default=False)


class AddressCreate(AddressBase):
    """Address creation schema."""
    pass


class AddressUpdate(BaseModel):
    """Address update schema."""
    label: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    street_address_1: Optional[str] = Field(None, max_length=255)
    street_address_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)
    phone: Optional[str] = Field(None, max_length=20)
    is_default: Optional[bool] = None


class AddressResponse(AddressBase):
    """Address response schema."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    """Base user schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """User creation schema."""
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_guest: bool = Field(default=False)
    session_id: Optional[str] = Field(None, max_length=255)


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserResponse(UserBase):
    """User response schema."""
    id: uuid.UUID
    is_guest: bool
    is_active: bool
    is_verified: bool
    is_admin: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    addresses: List[AddressResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserRegister(UserCreate):
    """User registration schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    is_guest: bool = Field(default=False)


class GuestUserCreate(BaseModel):
    """Guest user creation schema."""
    session_id: str = Field(..., max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseModel):
    """Password reset schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema."""
    email: EmailStr 