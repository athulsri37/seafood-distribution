from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus
from app.schemas.user import UserOut


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    status: OrderStatus
    # Statuses this order may move to next. Only staff can change a status.
    next_statuses: List[OrderStatus]
    total_amount: float
    customer: UserOut
    items: List[OrderItemOut]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
