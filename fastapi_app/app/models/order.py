from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETE = "complete"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    ref_code = Column(String(40), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_name = Column(String(100), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # Timing fields for analytics
    date_ordered = Column(DateTime(timezone=True), server_default=func.now())
    date_preparing = Column(DateTime(timezone=True), nullable=True)
    date_ready = Column(DateTime(timezone=True), nullable=True)
    date_complete = Column(DateTime(timezone=True), nullable=True)
    last_status_change = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, ref_code='{self.ref_code}', status='{self.status}')>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="order_items")
    food_item = relationship("FoodItem", lazy="select")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, food_item_id={self.food_item_id}, quantity={self.quantity})>"
