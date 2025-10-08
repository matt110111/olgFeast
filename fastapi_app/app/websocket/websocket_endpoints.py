"""
WebSocket endpoints for real-time communication
"""
from fastapi import WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
from datetime import datetime

from ..models.order import Order, OrderStatus
from ..schemas.websocket import (
    WebSocketMessage, 
    WebSocketMessageType,
    OrderUpdateMessage,
    KitchenUpdateMessage,
    ErrorMessage
)
from .connection_manager import manager
from ..services.order_service import OrderService
from ..core.database import get_db


async def kitchen_display_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for kitchen display updates
    Real-time updates for pending, preparing, and ready orders
    """
    # For now, allow connections without authentication for testing
    # In production, you would validate the token here
    await manager.connect(websocket, "kitchen_display")
    
    try:
        while True:
            # Wait for messages from client (ping, specific requests)
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                elif message_type == "request_update":
                    # Send current kitchen state
                    await send_kitchen_state_update(websocket)
                
            except json.JSONDecodeError:
                # Handle non-JSON messages
                if data.lower() == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


async def order_updates_websocket(
    websocket: WebSocket,
    user_id: Optional[int] = Query(None)
):
    """
    WebSocket endpoint for order status updates
    Real-time updates for specific user's orders
    """
    await manager.connect(websocket, "order_updates", {"user_id": user_id})
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                elif message_type == "subscribe_orders":
                    # Subscribe to specific user's order updates
                    target_user_id = message.get("user_id")
                    if target_user_id:
                        # Update connection info
                        manager.connection_info[websocket]["user_id"] = target_user_id
                        
                        # Send current orders
                        await send_user_orders_update(websocket, target_user_id)
                
            except json.JSONDecodeError:
                if data.lower() == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


async def admin_dashboard_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for admin dashboard updates
    Real-time analytics and management updates
    """
    # For now, allow connections without authentication for testing
    # In production, you would validate the token here
    await manager.connect(websocket, "admin_dashboard", {"is_admin": True})
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                
                elif message_type == "request_analytics":
                    await send_dashboard_analytics(websocket)
                
                elif message_type == "request_orders":
                    await send_all_orders_update(websocket)
                
            except json.JSONDecodeError:
                if data.lower() == "ping":
                    await manager.send_json_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


async def send_kitchen_state_update(websocket: WebSocket):
    """Send current kitchen state to a specific WebSocket"""
    from ..core.database import SessionLocal
    db = SessionLocal()
    order_service = OrderService(db)
    
    # Get orders by status
    pending_orders = order_service.get_orders_by_status(OrderStatus.PENDING)
    preparing_orders = order_service.get_orders_by_status(OrderStatus.PREPARING)
    ready_orders = order_service.get_orders_by_status(OrderStatus.READY)
    
    # Convert to WebSocket message format
    pending_data = [format_order_for_kitchen(order) for order in pending_orders]
    preparing_data = [format_order_for_kitchen(order) for order in preparing_orders]
    ready_data = [format_order_for_kitchen(order) for order in ready_orders]
    
    kitchen_update = KitchenUpdateMessage(
        pending_orders=pending_data,
        preparing_orders=preparing_data,
        ready_orders=ready_data,
        timestamp=datetime.utcnow()
    )
    
    await manager.send_json_message({
        "type": "kitchen_update",
        "data": kitchen_update.model_dump(),
        "timestamp": datetime.utcnow().isoformat()
    }, websocket)
    
    db.close()


async def send_user_orders_update(websocket: WebSocket, user_id: int):
    """Send user's current orders to WebSocket"""
    from ..core.database import SessionLocal
    db = SessionLocal()
    order_service = OrderService(db)
    orders = order_service.get_user_orders(user_id, limit=10)
    
    orders_data = []
    for order in orders:
        total_value = sum(item.food_item.value * item.quantity for item in order.order_items)
        total_tickets = sum(item.food_item.ticket * item.quantity for item in order.order_items)
        
        order_data = OrderUpdateMessage(
            order_id=order.id,
            ref_code=order.ref_code,
            customer_name=order.customer_name,
            status=order.status.value,
            total_value=total_value,
            total_tickets=total_tickets,
            item_count=len(order.order_items),
            date_ordered=order.date_ordered,
            date_preparing=order.date_preparing,
            date_ready=order.date_ready,
            date_complete=order.date_complete
        )
        orders_data.append(order_data.model_dump())
    
    await manager.send_json_message({
        "type": "user_orders_update",
        "data": {"orders": orders_data},
        "timestamp": datetime.utcnow().isoformat()
    }, websocket)
    
    db.close()


async def send_dashboard_analytics(websocket: WebSocket):
    """Send dashboard analytics to WebSocket"""
    from ..core.database import SessionLocal
    db = SessionLocal()
    order_service = OrderService(db)
    analytics = order_service.get_order_analytics()
    
    await manager.send_json_message({
        "type": "dashboard_analytics",
        "data": analytics,
        "timestamp": datetime.utcnow().isoformat()
    }, websocket)
    
    db.close()


async def send_all_orders_update(websocket: WebSocket):
    """Send all orders to WebSocket"""
    from ..core.database import SessionLocal
    db = SessionLocal()
    order_service = OrderService(db)
    orders = order_service.get_orders(limit=50)
    
    orders_data = []
    for order in orders:
        total_value = sum(item.food_item.value * item.quantity for item in order.order_items)
        total_tickets = sum(item.food_item.ticket * item.quantity for item in order.order_items)
        
        # Prepare order items data
        order_items_data = []
        for item in order.order_items:
            order_items_data.append({
                "food_item": {
                    "name": item.food_item.name,
                    "value": item.food_item.value
                },
                "quantity": item.quantity
            })
        
        order_data = OrderUpdateMessage(
            id=order.id,
            ref_code=order.ref_code,
            customer_name=order.customer_name,
            status=order.status.value,
            total_value=total_value,
            total_tickets=total_tickets,
            item_count=len(order.order_items),
            date_ordered=order.date_ordered,
            date_preparing=order.date_preparing,
            date_ready=order.date_ready,
            date_complete=order.date_complete,
            order_items=order_items_data
        )
        orders_data.append(order_data.model_dump())
    
    await manager.send_json_message({
        "type": "all_orders_update",
        "data": {"orders": orders_data},
        "timestamp": datetime.utcnow().isoformat()
    }, websocket)
    
    db.close()


def format_order_for_kitchen(order: Order) -> dict:
    """Format order data for kitchen display"""
    total_value = sum(item.food_item.value * item.quantity for item in order.order_items)
    total_tickets = sum(item.food_item.ticket * item.quantity for item in order.order_items)
    
    # Group items by food item for display
    items_summary = {}
    for item in order.order_items:
        food_name = item.food_item.name
        if food_name in items_summary:
            items_summary[food_name] += item.quantity
        else:
            items_summary[food_name] = item.quantity
    
    return {
        "id": order.id,
        "display_id": order.display_id,
        "ref_code": order.ref_code,
        "customer_name": order.customer_name,
        "status": order.status.value,
        "total_value": total_value,
        "total_tickets": total_tickets,
        "item_count": len(order.order_items),
        "items_summary": items_summary,
        "date_ordered": order.date_ordered.isoformat(),
        "date_preparing": order.date_preparing.isoformat() if order.date_preparing else None,
        "date_ready": order.date_ready.isoformat() if order.date_ready else None,
        "date_complete": order.date_complete.isoformat() if order.date_complete else None,
        "waiting_time": calculate_waiting_time(order)
    }


def calculate_waiting_time(order: Order) -> int:
    """Calculate waiting time in minutes"""
    from datetime import datetime
    
    now = datetime.utcnow()
    
    # Make sure both datetimes are naive (no timezone info)
    if order.date_ordered.tzinfo is not None:
        order_date = order.date_ordered.replace(tzinfo=None)
    else:
        order_date = order.date_ordered
    
    if order.status == OrderStatus.PENDING:
        return int((now - order_date).total_seconds() / 60)
    elif order.status == OrderStatus.PREPARING and order.date_preparing:
        prep_date = order.date_preparing.replace(tzinfo=None) if order.date_preparing.tzinfo else order.date_preparing
        return int((now - prep_date).total_seconds() / 60)
    elif order.status == OrderStatus.READY and order.date_ready:
        ready_date = order.date_ready.replace(tzinfo=None) if order.date_ready.tzinfo else order.date_ready
        return int((now - ready_date).total_seconds() / 60)
    else:
        return 0
