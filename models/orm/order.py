"""
Order domain SQLAlchemy models.
"""

from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, ForeignKey, Index, Integer, DECIMAL, JSON, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    """Order model."""
    
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
    
    # Order identification
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Order status
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="pending"
    )  # pending, confirmed, processing, shipped, delivered, cancelled, refunded
    
    # Pricing
    subtotal: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal('0.00'))
    shipping_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal('0.00'))
    discount_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=Decimal('0.00'))
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Shipping information
    shipping_address: Mapped[dict] = mapped_column(JSON, nullable=False)
    billing_address: Mapped[dict] = mapped_column(JSON, nullable=False)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Payment information
    payment_status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="pending"
    )  # pending, processing, completed, failed, refunded
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Discount code
    discount_code_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discountcode.id"),
        nullable=True
    )
    
    # Order dates
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes and special instructions
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    discount_code: Mapped[Optional["DiscountCode"]] = relationship("DiscountCode")
    
    # Indexes
    __table_args__ = (
        Index('ix_order_user_id', 'user_id'),
        Index('ix_order_number', 'order_number'),
        Index('ix_order_status', 'status'),
        Index('ix_order_payment_status', 'payment_status'),
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"


class OrderItem(Base, TimestampMixin):
    """Order item model."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order.id"),
        nullable=False
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productvariant.id"),
        nullable=False
    )
    
    # Product information (snapshot at time of order)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    variant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Quantity and pricing
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Customization data (JSON field)
    customizations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Total price including customizations
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product_variant: Mapped["ProductVariant"] = relationship("ProductVariant")
    
    # Indexes
    __table_args__ = (
        Index('ix_orderitem_order_id', 'order_id'),
        Index('ix_orderitem_variant_id', 'product_variant_id'),
    )
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, quantity={self.quantity})>" 