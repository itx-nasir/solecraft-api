"""
Cart domain Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid

from .product import ProductVariantResponse


class CartItemCustomization(BaseModel):
    """Cart item customization schema."""
    customization_id: uuid.UUID
    type: str = Field(..., description="Customization type: text, image, select")
    value: Any = Field(..., description="Customization value")
    price: Decimal = Field(..., ge=0, description="Additional price for this customization")


class CartItemBase(BaseModel):
    """Base cart item schema."""
    product_variant_id: uuid.UUID
    quantity: int = Field(..., gt=0, le=100)
    customizations: Optional[List[CartItemCustomization]] = []


class CartItemCreate(CartItemBase):
    """Cart item creation schema."""
    pass


class CartItemUpdate(BaseModel):
    """Cart item update schema."""
    quantity: Optional[int] = Field(None, gt=0, le=100)
    customizations: Optional[List[CartItemCustomization]] = None


class CartItemResponse(BaseModel):
    """Cart item response schema."""
    id: uuid.UUID
    cart_id: uuid.UUID
    product_variant_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    customizations: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    product_variant: ProductVariantResponse

    model_config = ConfigDict(from_attributes=True)


class CartBase(BaseModel):
    """Base cart schema."""
    session_id: Optional[str] = None


class CartCreate(CartBase):
    """Cart creation schema."""
    pass


class CartResponse(BaseModel):
    """Cart response schema."""
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: Optional[str]
    items: List[CartItemResponse] = []
    total_items: int = Field(default=0, description="Total number of items")
    subtotal: Decimal = Field(default=Decimal('0.00'), description="Subtotal before taxes")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartSummary(BaseModel):
    """Cart summary schema."""
    total_items: int
    subtotal: Decimal
    estimated_tax: Decimal = Field(default=Decimal('0.00'))
    estimated_shipping: Decimal = Field(default=Decimal('0.00'))
    estimated_total: Decimal


class AddToCartRequest(BaseModel):
    """Add to cart request schema."""
    product_variant_id: uuid.UUID
    quantity: int = Field(..., gt=0, le=100)
    customizations: Optional[List[CartItemCustomization]] = []


class UpdateCartItemRequest(BaseModel):
    """Update cart item request schema."""
    quantity: int = Field(..., gt=0, le=100)
    customizations: Optional[List[CartItemCustomization]] = [] 