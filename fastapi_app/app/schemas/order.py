from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .menu import FoodItem


class OrderItemBase(BaseModel):
    food_item_id: int
    quantity: int = 1


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime
    food_item: FoodItem

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_name: str


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    customer_name: Optional[str] = None


class Order(OrderBase):
    id: int
    display_id: int
    ref_code: str
    user_id: int
    status: str
    date_ordered: datetime
    date_preparing: Optional[datetime] = None
    date_ready: Optional[datetime] = None
    date_complete: Optional[datetime] = None
    last_status_change: datetime
    order_items: List[OrderItem] = []

    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    id: int
    display_id: int
    ref_code: str
    customer_name: str
    status: str
    total_value: float
    total_tickets: int
    item_count: int
    date_ordered: datetime


class OrderAnalytics(BaseModel):
    total_orders: int
    orders_today: int
    orders_this_week: int
    orders_this_month: int
    status_counts: dict
    revenue_today: float
    revenue_this_week: float
    total_revenue: float
