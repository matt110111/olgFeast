from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, UniqueConstraint, Boolean
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
    display_id = Column(Integer, unique=True, nullable=False)  # Simple 1-999 ID for staff
    ref_code = Column(String(40), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_name = Column(String(100), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    room_id = Column(Integer, ForeignKey('event_rooms.id'), nullable=True, index=True)
    check_id = Column(Integer, ForeignKey('station_checks.id'), nullable=True, index=True)
    station_number = Column(Integer, nullable=True)
    event_id = Column(Integer, ForeignKey('dinner_events.id'), nullable=True, index=True)
    checkout_key = Column(String(80), nullable=True)
    checkout_fingerprint = Column(String(64), nullable=True)
    awaiting_tickets = Column(Boolean, nullable=False, default=False)
    tickets_confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    tickets_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    tickets_collected = Column(Integer, nullable=False, default=0)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    void_reason = Column(String(200), nullable=True)
    __table_args__ = (UniqueConstraint('user_id', 'checkout_key', name='uq_order_checkout'),)

    # Timing fields for analytics
    date_ordered = Column(DateTime(timezone=True), server_default=func.now())
    date_preparing = Column(DateTime(timezone=True), nullable=True)
    date_ready = Column(DateTime(timezone=True), nullable=True)
    date_complete = Column(DateTime(timezone=True), nullable=True)
    last_status_change = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, display_id={self.display_id}, ref_code='{self.ref_code}', status='{self.status}')>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_tickets = Column(Integer, nullable=False, default=0)
    unit_value = Column(Numeric(12, 2), nullable=False, default=0)
    recipe_recorded = Column(Boolean, nullable=False, default=False)
    item_name = Column(String(100), nullable=False, default='')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="order_items")
    food_item = relationship("FoodItem", lazy="select")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, food_item_id={self.food_item_id}, quantity={self.quantity})>"
