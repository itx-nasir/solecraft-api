"""
Order domain Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
import uuid

from .user import AddressResponse
from .product import ProductVariantResponse


OrderStatus = Literal["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"]
PaymentStatus = Literal["pending", "processing", "completed", "failed", "refunded"]


class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class OrderItemCreate(OrderItemBase):
    """Order item creation schema."""
    pass


class OrderItemResponse(BaseModel):
    """Order item response schema."""
    id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    variant_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    """Base order schema."""
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    shipping_method: Optional[str] = None
    customer_notes: Optional[str] = None


class OrderCreate(OrderBase):
    """Order creation schema."""
    items: List[OrderItemCreate]
    discount_code: Optional[str] = None


class OrderUpdate(BaseModel):
    """Order update schema (admin only)."""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response schema."""
    id: uuid.UUID
    user_id: uuid.UUID
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    shipping_method: Optional[str]
    tracking_number: Optional[str]
    payment_method: Optional[str]
    payment_provider: Optional[str]
    confirmed_at: Optional[datetime]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    notes: Optional[str]
    customer_notes: Optional[str]
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Order list response schema."""
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderSummary(BaseModel):
    """Order summary schema."""
    subtotal: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal


class CheckoutRequest(BaseModel):
    """Checkout request schema."""
    shipping_address_id: Optional[uuid.UUID] = None
    billing_address_id: Optional[uuid.UUID] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    shipping_method: Optional[str] = None
    payment_method: str
    discount_code: Optional[str] = None
    customer_notes: Optional[str] = None


class PaymentIntent(BaseModel):
    """Payment intent schema."""
    client_secret: str
    amount: Decimal
    currency: str = Field(default="usd")


class DiscountCodeBase(BaseModel):
    """Base discount code schema."""
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    discount_type: Literal["percentage", "fixed"]
    discount_value: Decimal = Field(..., gt=0)
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_discount_amount: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    usage_limit_per_user: Optional[int] = Field(None, gt=0)
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_active: bool = Field(default=True)


class DiscountCodeCreate(DiscountCodeBase):
    """Discount code creation schema."""
    pass


class DiscountCodeUpdate(BaseModel):
    """Discount code update schema."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    discount_type: Optional[Literal["percentage", "fixed"]] = None
    discount_value: Optional[Decimal] = Field(None, gt=0)
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_discount_amount: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    usage_limit_per_user: Optional[int] = Field(None, gt=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class DiscountCodeResponse(DiscountCodeBase):
    """Discount code response schema."""
    id: uuid.UUID
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscountValidation(BaseModel):
    """Discount validation response schema."""
    is_valid: bool
    discount_amount: Decimal = Field(default=Decimal('0.00'))
    message: str 