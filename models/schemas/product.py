"""
Product domain Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid


class ProductCustomizationBase(BaseModel):
    """Base product customization schema."""
    name: str = Field(..., max_length=100)
    type: str = Field(..., max_length=20)  # text, image, select
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(..., description="Customization configuration")
    base_price: Decimal = Field(default=Decimal('0.00'), ge=0)
    sort_order: int = Field(default=0)
    is_required: bool = Field(default=False)
    is_active: bool = Field(default=True)


class ProductCustomizationCreate(ProductCustomizationBase):
    """Product customization creation schema."""
    pass


class ProductCustomizationUpdate(BaseModel):
    """Product customization update schema."""
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    sort_order: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductCustomizationResponse(ProductCustomizationBase):
    """Product customization response schema."""
    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductVariantBase(BaseModel):
    """Base product variant schema."""
    sku: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=20)
    material: Optional[str] = Field(None, max_length=100)
    price_adjustment: Decimal = Field(default=Decimal('0.00'))
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    images: Optional[List[str]] = None
    is_active: bool = Field(default=True)


class ProductVariantCreate(ProductVariantBase):
    """Product variant creation schema."""
    pass


class ProductVariantUpdate(BaseModel):
    """Product variant update schema."""
    sku: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=20)
    material: Optional[str] = Field(None, max_length=100)
    price_adjustment: Optional[Decimal] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase):
    """Product variant response schema."""
    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=200)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    base_price: Decimal = Field(..., gt=0)
    is_active: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    is_customizable: bool = Field(default=True)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    specifications: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None


class ProductCreate(ProductBase):
    """Product creation schema."""
    pass


class ProductUpdate(BaseModel):
    """Product update schema."""
    name: Optional[str] = Field(None, max_length=200)
    slug: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    base_price: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_customizable: Optional[bool] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    specifications: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None


class ProductResponse(ProductBase):
    """Product response schema."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    variants: List[ProductVariantResponse] = []
    customizations: List[ProductCustomizationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Product list response schema."""
    id: uuid.UUID
    name: str
    slug: str
    short_description: Optional[str]
    base_price: Decimal
    is_featured: bool
    images: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)


class ProductSearchRequest(BaseModel):
    """Product search request schema."""
    query: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    color: Optional[str] = None
    size: Optional[str] = None
    is_featured: Optional[bool] = None
    is_customizable: Optional[bool] = None 