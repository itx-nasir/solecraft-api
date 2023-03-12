"""
Product domain SQLAlchemy models.
"""

from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, Index, Integer, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    """Product model for customizable shoes."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic product information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Pricing
    base_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Product status and visibility
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_customizable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Product specifications (JSON field for flexibility)
    specifications: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Images (JSON array of image URLs)
    images: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="product"
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_product_slug', 'slug'),
        Index('ix_product_is_active', 'is_active'),
        Index('ix_product_is_featured', 'is_featured'),
    )
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, slug={self.slug})>" 