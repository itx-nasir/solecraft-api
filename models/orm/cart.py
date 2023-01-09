"""
Cart domain SQLAlchemy models.
"""

from decimal import Decimal
from typing import List, Optional
from sqlalchemy import String, ForeignKey, Index, Integer, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class Cart(Base, TimestampMixin):
    """Shopping cart model."""
    
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
    
    # Session ID for guest users
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_cart_user_id', 'user_id'),
        Index('ix_cart_session_id', 'session_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id})>"


class CartItem(Base, TimestampMixin):
    """Cart item model with product variant and customization."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cart.id"),
        nullable=False
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("productvariant.id"),
        nullable=False
    )
    
    # Quantity and pricing
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Customization data (JSON field)
    # Structure: {
    #   "customization_id": {
    #     "type": "text",
    #     "value": "My Custom Text",
    #     "price": 5.00
    #   },
    #   ...
    # }
    customizations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Total price including customizations
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    product_variant: Mapped["ProductVariant"] = relationship("ProductVariant")
    
    # Indexes
    __table_args__ = (
        Index('ix_cartitem_cart_id', 'cart_id'),
        Index('ix_cartitem_variant_id', 'product_variant_id'),
    )
    
    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, cart_id={self.cart_id}, quantity={self.quantity})>" 