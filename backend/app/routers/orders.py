from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate, OrderItemOut
from app.services.orders import next_statuses, transition_error

router = APIRouter(prefix="/api/orders", tags=["orders"])

# Everything _serialize_order reads. Loading it up front takes one query per relationship,
# however many orders there are, instead of one per order (the N+1 problem).
ORDER_DETAILS = (
    selectinload(Order.customer),
    selectinload(Order.items).selectinload(OrderItem.product),
)


def _serialize_order(order: Order) -> OrderOut:
    items = [
        OrderItemOut(
            id=i.id,
            product_id=i.product_id,
            product_name=i.product.name,
            quantity=i.quantity,
            unit_price=float(i.unit_price),
        )
        for i in order.items
    ]
    return OrderOut(
        id=order.id,
        status=order.status,
        next_statuses=list(next_statuses(order.status)),
        total_amount=float(order.total_amount),
        customer=order.customer,
        items=items,
        created_at=order.created_at,
    )


def _deduct_stock(db: Session, product_id: int, quantity: int) -> Decimal:
    """Take `quantity` off the product's stock and return its current unit price.

    The stock check and the deduction are one UPDATE, so a concurrent order can't take
    the same units between them. Raises 404 for an unknown product and 409 when there
    isn't enough stock.
    """
    price = db.execute(
        update(Product)
        .where(Product.id == product_id, Product.quantity_on_hand >= quantity)
        .values(quantity_on_hand=Product.quantity_on_hand - quantity)
        .returning(Product.price_per_unit)
    ).scalar_one_or_none()
    if price is not None:
        return price

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    raise HTTPException(
        status_code=409,
        detail=f"Insufficient stock for {product.name} (available: {product.quantity_on_hand})",
    )


@router.get("", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Order).options(*ORDER_DETAILS)
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Order.customer_id == current_user.id)
    orders = query.order_by(Order.created_at.desc()).all()
    return [_serialize_order(o) for o in orders]


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    order = Order(customer_id=current_user.id, status=OrderStatus.PENDING, total_amount=0)
    db.add(order)
    db.flush()

    # Deduct stock in product-id order so two orders sharing products always lock their
    # rows in the same order and can't deadlock.
    prices: dict[int, Decimal] = {}
    for item in sorted(payload.items, key=lambda i: i.product_id):
        prices[item.product_id] = _deduct_stock(db, item.product_id, item.quantity)

    total = 0.0
    for item in payload.items:
        unit_price = float(prices[item.product_id])
        total += unit_price * item.quantity

        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=unit_price,
            )
        )

    order.total_amount = total
    db.commit()
    db.refresh(order)
    return _serialize_order(order)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRIBUTOR)),
):
    # Lock the order so simultaneous status changes run one at a time and each one
    # checks the rules against the status the previous one left behind.
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if payload.status == order.status:
        # Setting the current status again (a retry, or a second click) changes nothing.
        return _serialize_order(order)
    if payload.status not in next_statuses(order.status):
        raise HTTPException(status_code=409, detail=transition_error(order.id, order.status, payload.status))

    if payload.status == OrderStatus.CANCELLED:
        for item in sorted(order.items, key=lambda i: i.product_id):
            # Add in SQL, not in Python, so stock deducted by concurrent orders isn't overwritten.
            db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(quantity_on_hand=Product.quantity_on_hand + item.quantity)
            )

    order.status = payload.status
    db.commit()
    db.refresh(order)
    return _serialize_order(order)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    order = db.query(Order).options(*ORDER_DETAILS).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    return _serialize_order(order)
