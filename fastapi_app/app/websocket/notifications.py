"""Run broadcasts on the application's event loop after committed writes."""
import logging
from ..core.database import SessionLocal
from ..models.order import Order
from .websocket_service import WebSocketService
from .connection_manager import manager


async def notify_order(order_id):
    if not any(manager.active_connections.values()):
        return
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        if not order:
            return
        try:
            service = WebSocketService(db)
            if manager.active_connections.get('kitchen_display'):
                await service.broadcast_kitchen_update()
            if manager.active_connections.get('admin_dashboard'):
                await service.broadcast_dashboard_update()
            await service._broadcast_to_user_orders(order.user_id, {'type': 'order_status_change',
                'data': {'order_id': order.id, 'status': order.status.value}})
        except Exception:
            logging.getLogger(__name__).exception('Order saved, but live notification failed')
