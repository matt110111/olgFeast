from pydantic import BaseModel, Field
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
    unit_tickets: int
    unit_value: float
    item_name: str
    recipe_recorded: bool = False

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)


class OrderCreate(OrderBase):
    checkout_key: Optional[str] = Field(default=None, min_length=8, max_length=80)


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
    event_id: Optional[int] = None
    room_id: Optional[int] = None
    check_id: Optional[int] = None
    station_number: Optional[int] = None
    awaiting_tickets: bool = False
    tickets_confirmed_by: Optional[int] = None
    tickets_confirmed_at: Optional[datetime] = None
    tickets_collected: int = 0
    voided_at: Optional[datetime] = None
    void_reason: Optional[str] = None
    order_items: List[OrderItem] = []

    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    awaiting_tickets: bool = False
    voided_at: Optional[datetime] = None
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
