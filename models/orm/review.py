"""
Review and DiscountCode SQLAlchemy models.
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy import String, ForeignKey, Index, Integer, DECIMAL, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    """Product review model."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id"),
        nullable=False
    )
    
    # Review content
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Review status
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Helpfulness tracking
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    
    # Indexes
    __table_args__ = (
        Index('ix_review_user_id', 'user_id'),
        Index('ix_review_product_id', 'product_id'),
        Index('ix_review_rating', 'rating'),
        Index('ix_review_is_approved', 'is_approved'),
    )
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, product_id={self.product_id}, rating={self.rating})>"


class DiscountCode(Base, TimestampMixin):
    """Discount code model."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Code details
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Discount type and value
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # percentage, fixed
    discount_value: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Usage restrictions
    minimum_order_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    maximum_discount_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_limit_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Time restrictions
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status and tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('ix_discount_code', 'code'),
        Index('ix_discount_is_active', 'is_active'),
        Index('ix_discount_valid_from', 'valid_from'),
        Index('ix_discount_valid_until', 'valid_until'),
    )
    
    def __repr__(self) -> str:
        return f"<DiscountCode(id={self.id}, code={self.code}, type={self.discount_type})>" 