from datetime import datetime
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

# Upper bounds match the database columns, so out-of-range input gets a 422 instead of
# a database error.
MAX_PRICE = 99_999_999.99  # NUMERIC(10, 2)
MAX_COUNT = 2_147_483_647  # INTEGER


def _at_most_two_decimals(value: float) -> float:
    # NUMERIC(10, 2) would silently round 0.001 down to 0.00.
    if round(value, 2) != value:
        raise ValueError("must have at most 2 decimal places")
    return value


Text = Annotated[str, Field(min_length=1)]  # surrounding spaces are stripped first
Price = Annotated[float, Field(gt=0, le=MAX_PRICE), AfterValidator(_at_most_two_decimals)]
Count = Annotated[int, Field(ge=0, le=MAX_COUNT)]


class ProductCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Text
    species: Text
    sku: Text
    unit: Text = "lb"
    price_per_unit: Price
    quantity_on_hand: Count = 0
    reorder_threshold: Count = 50
    warehouse_location: Optional[str] = None


class ProductUpdate(BaseModel):
    """Fields left out keep their current value. Only warehouse_location can be cleared."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[Text] = None
    price_per_unit: Optional[Price] = None
    quantity_on_hand: Optional[Count] = None
    reorder_threshold: Optional[Count] = None
    warehouse_location: Optional[str] = None

    # Runs only for fields the request actually sent, so an explicit null is caught
    # while a missing field still means "unchanged".
    @field_validator("name", "price_per_unit", "quantity_on_hand", "reorder_threshold")
    @classmethod
    def _required_fields_cannot_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("can't be null; leave the field out to keep the current value")
        return value


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
