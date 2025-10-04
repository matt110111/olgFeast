"""
WebSocket message schemas for real-time communication
"""
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""
    ORDER_UPDATE = "order_update"
    ORDER_STATUS_CHANGE = "order_status_change"
    NEW_ORDER = "new_order"
    KITCHEN_UPDATE = "kitchen_update"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """Base WebSocket message schema"""
    type: WebSocketMessageType
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()
    message: Optional[str] = None


class OrderUpdateMessage(BaseModel):
    """Order update WebSocket message"""
    order_id: int
    ref_code: str
    customer_name: str
    status: str
    total_value: float
    total_tickets: int
    item_count: int
    date_ordered: datetime
    date_preparing: Optional[datetime] = None
    date_ready: Optional[datetime] = None
    date_complete: Optional[datetime] = None


class OrderStatusChangeMessage(BaseModel):
    """Order status change WebSocket message"""
    order_id: int
    ref_code: str
    old_status: str
    new_status: str
    timestamp: datetime
    customer_name: str


class NewOrderMessage(BaseModel):
    """New order WebSocket message"""
    order_id: int
    ref_code: str
    customer_name: str
    total_value: float
    total_tickets: int
    item_count: int
    timestamp: datetime


class KitchenUpdateMessage(BaseModel):
    """Kitchen display update message"""
    pending_orders: list
    preparing_orders: list
    ready_orders: list
    timestamp: datetime


class ErrorMessage(BaseModel):
    """Error WebSocket message"""
    error_code: str
    error_message: str
    timestamp: datetime
