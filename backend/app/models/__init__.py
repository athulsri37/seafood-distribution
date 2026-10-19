"""Importing this package registers every model on Base.metadata.

Relationships refer to other models by name ("Order", "User"), so all of them must be
imported before the first query. Anything that needs the full schema (Alembic, scripts)
imports `app.models` rather than individual modules.
"""
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole

__all__ = ["Order", "OrderItem", "OrderStatus", "Product", "User", "UserRole"]
