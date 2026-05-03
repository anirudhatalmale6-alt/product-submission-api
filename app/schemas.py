from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100, description="Unique product SKU")
    title: str = Field(..., min_length=1, max_length=500, description="Product title")
    description: Optional[str] = Field(None, description="Product description (HTML supported)")
    price: float = Field(..., gt=0, description="Product price")
    currency: str = Field("GBP", max_length=10, description="Currency code")
    quantity: int = Field(0, ge=0, description="Stock quantity")
    images: List[str] = Field(default_factory=list, description="List of image URLs")
    category: Optional[str] = Field(None, max_length=255, description="Product category")
    item_specifics: Dict[str, Any] = Field(default_factory=dict, description="eBay item specifics (key-value pairs)")
    condition: str = Field("New", max_length=50, description="Item condition")
    brand: Optional[str] = Field(None, max_length=255, description="Brand name")
    mpn: Optional[str] = Field(None, max_length=100, description="Manufacturer Part Number")
    ean: Optional[str] = Field(None, max_length=50, description="EAN/barcode")
    weight: Optional[float] = Field(None, ge=0, description="Weight in kg")

    @field_validator("images")
    @classmethod
    def validate_images(cls, v):
        if len(v) > 24:
            raise ValueError("Maximum 24 images allowed")
        return v


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=10)
    quantity: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=255)
    item_specifics: Optional[Dict[str, Any]] = None
    condition: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=255)
    mpn: Optional[str] = Field(None, max_length=100)
    ean: Optional[str] = Field(None, max_length=50)
    weight: Optional[float] = Field(None, ge=0)


class ProductResponse(BaseModel):
    id: int
    sku: str
    title: str
    description: Optional[str]
    price: float
    currency: str
    quantity: int
    images: List[str]
    category: Optional[str]
    item_specifics: Dict[str, Any]
    condition: str
    brand: Optional[str]
    mpn: Optional[str]
    ean: Optional[str]
    weight: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkProductCreate(BaseModel):
    products: List[ProductCreate] = Field(..., min_length=1, max_length=100, description="List of products (max 100 per request)")


class BulkProductResponse(BaseModel):
    successful: int
    failed: int
    products: List[ProductResponse]
    errors: List[Dict[str, Any]]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class ErrorResponse(BaseModel):
    detail: str
    errors: Optional[List[Dict[str, Any]]] = None
