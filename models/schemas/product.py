"""
Product domain Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import uuid


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