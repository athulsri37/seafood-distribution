from sqlalchemy import CheckConstraint, Column, Integer, String, Numeric, DateTime, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        # Last line of defence: whatever the code does, stock can never go below zero.
        CheckConstraint("quantity_on_hand >= 0", name="quantity_on_hand_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    unit = Column(String, nullable=False, default="lb")
    price_per_unit = Column(Numeric(10, 2), nullable=False)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=50)
    warehouse_location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    order_items = relationship("OrderItem", back_populates="product")

    # A hybrid works both on a loaded product (True/False) and in a query
    # (Product.is_low_stock becomes `quantity_on_hand <= reorder_threshold` in SQL),
    # so the rule is written once.
    @hybrid_property
    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.reorder_threshold
