from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.report import DashboardSummary, SalesByStatus, TopProduct

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DISTRIBUTOR)),
):
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0
    total_customers = (
        db.query(func.count(User.id)).filter(User.role == UserRole.CUSTOMER).scalar() or 0
    )

    products = db.query(Product).all()
    low_stock_count = sum(1 for p in products if p.is_low_stock)

    status_rows = (
        db.query(Order.status, func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0))
        .group_by(Order.status)
        .all()
    )
    sales_by_status = [
        SalesByStatus(status=s.value, order_count=c, total_revenue=float(r)) for s, c, r in status_rows
    ]

    top_rows = (
        db.query(
            Product.name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    top_products = [
        TopProduct(product_name=name, units_sold=int(units), revenue=float(revenue))
        for name, units, revenue in top_rows
    ]

    return DashboardSummary(
        total_orders=total_orders,
        total_revenue=float(total_revenue),
        total_customers=total_customers,
        low_stock_count=low_stock_count,
        sales_by_status=sales_by_status,
        top_products=top_products,
    )
