"""
User domain SQLAlchemy models.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model supporting both registered and guest users."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    addresses: Mapped[List["Address"]] = relationship(
        "Address", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    cart: Mapped[Optional["Cart"]] = relationship(
        "Cart", 
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('ix_user_email', 'email'),
        Index('ix_user_session_id', 'session_id'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_guest={self.is_guest})>"


class Address(Base, TimestampMixin):
    """User address model."""
    
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
    
    # Address details
    label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "Home", "Work"
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    street_address_1: Mapped[str] = mapped_column(String(255), nullable=False)
    street_address_2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Default address flag
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    
    def __repr__(self) -> str:
        return f"<Address(id={self.id}, user_id={self.user_id}, label={self.label})>" 