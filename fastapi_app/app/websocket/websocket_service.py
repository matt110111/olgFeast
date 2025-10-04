"""
WebSocket service for broadcasting messages and managing real-time updates
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.order import Order, OrderStatus
from ..schemas.websocket import (
    WebSocketMessage,
    WebSocketMessageType,
    OrderStatusChangeMessage,
    NewOrderMessage,
    KitchenUpdateMessage
)
from .connection_manager import manager


class WebSocketService:
    """Service for WebSocket broadcasting and notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def broadcast_order_status_change(
        self, 
        order: Order, 
        old_status: OrderStatus, 
        new_status: OrderStatus
    ):
        """Broadcast order status change to relevant channels"""
        
        # Create status change message
        status_change = OrderStatusChangeMessage(
            order_id=order.id,
            ref_code=order.ref_code,
            old_status=old_status.value,
            new_status=new_status.value,
            timestamp=datetime.utcnow(),
            customer_name=order.customer_name
        )
        
        # Broadcast to kitchen display
        await manager.broadcast_json_to_channel({
            "type": "order_status_change",
            "data": status_change.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }, "kitchen_display")
        
        # Broadcast to admin dashboard
        await manager.broadcast_json_to_channel({
            "type": "order_status_change",
            "data": status_change.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }, "admin_dashboard")
        
        # Broadcast to user's order updates (if user is connected)
        await self._broadcast_to_user_orders(order.user_id, {
            "type": "order_status_change",
            "data": status_change.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send updated kitchen state
        await self.broadcast_kitchen_update()
        
        print(f"📢 Broadcasted order {order.ref_code} status change: {old_status.value} → {new_status.value}")
    
    async def broadcast_new_order(self, order: Order):
        """Broadcast new order to relevant channels"""
        
        # Calculate order totals
        total_value = sum(item.food_item.value * item.quantity for item in order.order_items)
        total_tickets = sum(item.food_item.ticket * item.quantity for item in order.order_items)
        
        # Create new order message
        new_order = NewOrderMessage(
            order_id=order.id,
            ref_code=order.ref_code,
            customer_name=order.customer_name,
            total_value=total_value,
            total_tickets=total_tickets,
            item_count=len(order.order_items),
            timestamp=datetime.utcnow()
        )
        
        # Broadcast to kitchen display
        await manager.broadcast_json_to_channel({
            "type": "new_order",
            "data": new_order.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }, "kitchen_display")
        
        # Broadcast to admin dashboard
        await manager.broadcast_json_to_channel({
            "type": "new_order",
            "data": new_order.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }, "admin_dashboard")
        
        # Send updated kitchen state
        await self.broadcast_kitchen_update()
        
        print(f"📢 Broadcasted new order: {order.ref_code}")
    
    async def broadcast_kitchen_update(self):
        """Broadcast updated kitchen state to kitchen display"""
        
        # Get current kitchen state
        pending_orders = self.db.query(Order).filter(Order.status == OrderStatus.PENDING).order_by(Order.date_ordered).all()
        preparing_orders = self.db.query(Order).filter(Order.status == OrderStatus.PREPARING).order_by(Order.date_ordered).all()
        ready_orders = self.db.query(Order).filter(Order.status == OrderStatus.READY).order_by(Order.date_ordered).all()
        
        # Format orders for kitchen display
        pending_data = [self._format_order_for_kitchen(order) for order in pending_orders]
        preparing_data = [self._format_order_for_kitchen(order) for order in preparing_orders]
        ready_data = [self._format_order_for_kitchen(order) for order in ready_orders]
        
        # Create kitchen update message
        kitchen_update = KitchenUpdateMessage(
            pending_orders=pending_data,
            preparing_orders=preparing_data,
            ready_orders=ready_data,
            timestamp=datetime.utcnow()
        )
        
        # Broadcast to kitchen display
        await manager.broadcast_json_to_channel({
            "type": "kitchen_update",
            "data": kitchen_update.model_dump(),
            "timestamp": datetime.utcnow().isoformat()
        }, "kitchen_display")
        
        print(f"📢 Broadcasted kitchen update: {len(pending_data)} pending, {len(preparing_data)} preparing, {len(ready_data)} ready")
    
    async def broadcast_dashboard_update(self):
        """Broadcast dashboard analytics update"""
        
        # Get analytics data
        analytics = self._get_dashboard_analytics()
        
        # Broadcast to admin dashboard
        await manager.broadcast_json_to_channel({
            "type": "dashboard_update",
            "data": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }, "admin_dashboard")
        
        print("📊 Broadcasted dashboard update")
    
    async def _broadcast_to_user_orders(self, user_id: int, message: dict):
        """Broadcast message to user's order updates channel"""
        
        # Find connections for this user
        connections_to_notify = []
        
        for websocket, info in manager.connection_info.items():
            if (info.get("channel") == "order_updates" and 
                info.get("user_id") == user_id):
                connections_to_notify.append(websocket)
        
        # Send message to user's connections
        for websocket in connections_to_notify:
            try:
                await manager.send_json_message(message, websocket)
            except Exception as e:
                print(f"❌ Error sending to user {user_id}: {e}")
                await manager.disconnect(websocket)
    
    def _format_order_for_kitchen(self, order: Order) -> dict:
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
            "waiting_time": self._calculate_waiting_time(order)
        }
    
    def _calculate_waiting_time(self, order: Order) -> int:
        """Calculate waiting time in minutes"""
        
        now = datetime.utcnow()
        
        if order.status == OrderStatus.PENDING:
            return int((now - order.date_ordered).total_seconds() / 60)
        elif order.status == OrderStatus.PREPARING and order.date_preparing:
            return int((now - order.date_preparing).total_seconds() / 60)
        elif order.status == OrderStatus.READY and order.date_ready:
            return int((now - order.date_ready).total_seconds() / 60)
        else:
            return 0
    
    def _get_dashboard_analytics(self) -> dict:
        """Get dashboard analytics data"""
        
        from datetime import timedelta
        
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Basic statistics
        total_orders = self.db.query(Order).count()
        orders_today = self.db.query(Order).filter(Order.date_ordered >= last_24h).count()
        orders_this_week = self.db.query(Order).filter(Order.date_ordered >= last_7d).count()
        
        # Status counts
        status_counts = {}
        for status in OrderStatus:
            count = self.db.query(Order).filter(Order.status == status).count()
            status_counts[status.value] = count
        
        # Revenue calculations
        completed_orders = self.db.query(Order).filter(Order.status == OrderStatus.COMPLETE)
        
        total_revenue = 0
        revenue_today = 0
        
        for order in completed_orders:
            order_value = sum(item.food_item.value * item.quantity for item in order.order_items)
            total_revenue += order_value
            
            if order.date_ordered >= last_24h:
                revenue_today += order_value
        
        return {
            "total_orders": total_orders,
            "orders_today": orders_today,
            "orders_this_week": orders_this_week,
            "status_counts": status_counts,
            "total_revenue": round(total_revenue, 2),
            "revenue_today": round(revenue_today, 2)
        }
