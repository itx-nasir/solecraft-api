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
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    customizations: Mapped[List["ProductCustomization"]] = relationship(
        "ProductCustomization",
        back_populates="product",
        cascade="all, delete-orphan"
    )
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


class ProductVariant(Base, TimestampMixin):
    """Product variant model for different colors, sizes, etc."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id"),
        nullable=False
    )
    
    # Variant details
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g., "Red - Size 42"
    
    # Variant attributes
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Pricing and inventory
    price_adjustment: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), 
        default=Decimal('0.00'), 
        nullable=False
    )
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    
    # Variant images
    images: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    
    # Indexes
    __table_args__ = (
        Index('ix_variant_product_id', 'product_id'),
        Index('ix_variant_sku', 'sku'),
        Index('ix_variant_is_active', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, sku={self.sku}, name={self.name})>"


class ProductCustomization(Base, TimestampMixin):
    """Product customization options (text, image, select)."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id"),
        nullable=False
    )
    
    # Customization details
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Text on side"
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # text, image, select
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration (JSON field for flexibility)
    # For text: {"max_length": 20, "font_options": [...]}
    # For select: {"options": [{"value": "red", "label": "Red", "price": 5.00}]}
    # For image: {"max_size": 5242880, "allowed_formats": ["jpg", "png"]}
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Pricing
    base_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), 
        default=Decimal('0.00'), 
        nullable=False
    )
    
    # Display order and status
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="customizations")
    
    def __repr__(self) -> str:
        return f"<ProductCustomization(id={self.id}, name={self.name}, type={self.type})>" 