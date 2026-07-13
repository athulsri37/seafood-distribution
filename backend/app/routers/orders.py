from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate, OrderItemOut

router = APIRouter(prefix="/api/orders", tags=["orders"])


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
        total_amount=float(order.total_amount),
        customer=order.customer,
        items=items,
        created_at=order.created_at,
    )


@router.get("", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Order)
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

    total = 0.0
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.quantity_on_hand < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name} (available: {product.quantity_on_hand})",
            )
        product.quantity_on_hand -= item.quantity
        unit_price = float(product.price_per_unit)
        total += unit_price * item.quantity

        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
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
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if payload.status == OrderStatus.CANCELLED and order.status != OrderStatus.CANCELLED:
        for item in order.items:
            item.product.quantity_on_hand += item.quantity

    order.status = payload.status
    db.commit()
    db.refresh(order)
    return _serialize_order(order)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role == UserRole.CUSTOMER and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    return _serialize_order(order)
