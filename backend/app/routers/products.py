from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import BigInteger, cast, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles, get_current_user
from app.models.product import Product
from app.models.user import UserRole, User
from app.schemas.product import MAX_COUNT, ProductCreate, ProductOut, ProductUpdate, StockAdjustment

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=List[ProductOut])
def list_products(
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Product)
    products = query.all()
    if low_stock_only:
        products = [p for p in products if p.is_low_stock]
    return products


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRIBUTOR)),
):
    existing = db.query(Product).filter(Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRIBUTOR)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.post("/{product_id}/stock-adjustments", response_model=ProductOut)
def adjust_stock(
    product_id: int,
    payload: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRIBUTOR)),
):
    """Add or remove units. Simultaneous adjustments add up instead of overwriting each other."""
    # Apply the change in SQL, as one statement with its own range check. The check is
    # done in BIGINT so a huge change can't overflow the INTEGER column mid-comparison.
    new_quantity = cast(Product.quantity_on_hand, BigInteger) + payload.change
    adjusted = db.execute(
        update(Product)
        .where(Product.id == product_id, new_quantity >= 0, new_quantity <= MAX_COUNT)
        .values(quantity_on_hand=Product.quantity_on_hand + payload.change)
        .returning(Product.id)
    ).scalar_one_or_none()

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if adjusted is None:
        if payload.change < 0:
            detail = (
                f"Can't remove {-payload.change} {product.unit}: only {product.quantity_on_hand} "
                f"{product.unit} of {product.name} in stock."
            )
        else:
            detail = f"Can't add {payload.change} {product.unit}: stock would exceed {MAX_COUNT}."
        raise HTTPException(status_code=409, detail=detail)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
