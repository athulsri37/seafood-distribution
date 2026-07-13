from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    species: str
    sku: str
    unit: str = "lb"
    price_per_unit: float = Field(gt=0)
    quantity_on_hand: int = Field(ge=0, default=0)
    reorder_threshold: int = Field(ge=0, default=50)
    warehouse_location: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price_per_unit: Optional[float] = None
    quantity_on_hand: Optional[int] = None
    reorder_threshold: Optional[int] = None
    warehouse_location: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    species: str
    sku: str
    unit: str
    price_per_unit: float
    quantity_on_hand: int
    reorder_threshold: int
    warehouse_location: Optional[str]
    is_low_stock: bool
    created_at: datetime

    class Config:
        from_attributes = True
