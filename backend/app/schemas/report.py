from typing import List

from pydantic import BaseModel


class SalesByStatus(BaseModel):
    status: str
    order_count: int
    total_revenue: float


class TopProduct(BaseModel):
    product_name: str
    sku: str
    units_sold: int
    revenue: float


class DashboardSummary(BaseModel):
    total_orders: int
    total_revenue: float
    total_customers: int
    low_stock_count: int
    sales_by_status: List[SalesByStatus]
    top_products: List[TopProduct]
