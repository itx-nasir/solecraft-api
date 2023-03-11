"""
Common Pydantic schemas.
"""

from datetime import datetime
from typing import List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field, ConfigDict
import uuid


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters schema."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema."""
    items: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class SuccessResponse(BaseModel):
    """Generic success response schema."""
    success: bool = Field(default=True)
    message: str
    data: Optional[dict] = None


class StandardResponse(BaseModel, Generic[T]):
    """Standard API response schema with typed data."""
    success: bool = Field(default=True)
    message: str
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = Field(default=False)
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


class HealthCheck(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy")
    timestamp: datetime
    version: str
    database: str = Field(default="connected")
    scheduler: str = Field(default="running")
    environment: str = Field(default="development")
    port: str = Field(default="8000")
    missing_env_vars: Optional[List[str]] = None


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Optional[dict] = None


class TokenData(BaseModel):
    """Schema for data contained within a JWT."""
    user_id: str
    email: Optional[str] = None
    is_guest: bool = False
    session_id: Optional[str] = None
    scope: Optional[str] = None


class ReviewBase(BaseModel):
    """Base schema for a review."""
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Review creation schema."""
    product_id: uuid.UUID


class ReviewUpdate(BaseModel):
    """Review update schema."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = None


class ReviewResponse(ReviewBase):
    """Review response schema."""
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    is_verified_purchase: bool
    is_approved: bool
    is_featured: bool
    helpful_count: int
    not_helpful_count: int
    created_at: datetime
    updated_at: datetime
    user: Optional[dict] = None  # Basic user info without sensitive data

    model_config = ConfigDict(from_attributes=True)


class ReviewHelpfulness(BaseModel):
    """Review helpfulness action schema."""
    helpful: bool = Field(..., description="True for helpful, False for not helpful")


class FileUploadResponse(BaseModel):
    """File upload response schema."""
    filename: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_at: datetime


class BulkActionRequest(BaseModel):
    """Bulk action request schema."""
    action: str = Field(..., description="Action to perform")
    ids: List[uuid.UUID] = Field(..., min_items=1, description="List of item IDs")
    
    
class BulkActionResponse(BaseModel):
    """Bulk action response schema."""
    success_count: int
    failed_count: int
    failed_ids: List[uuid.UUID] = []
    messages: List[str] = []


class SearchFilters(BaseModel):
    """Common search filters schema."""
    query: Optional[str] = Field(None, description="Search query")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Sort order")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None 