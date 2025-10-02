import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from shopping_cart.models import Transaction


class KitchenDisplayConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.station = self.scope['url_route']['kwargs']['station']
        self.room_group_name = f'kitchen_{self.station}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_orders()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'request_update':
            await self.send_initial_orders()
    
    async def send_initial_orders(self):
        """Send current orders for this station"""
        orders = await self.get_orders_for_station()
        await self.send(text_data=json.dumps({
            'type': 'orders_update',
            'orders': orders,
            'station': self.station
        }))
    
    async def order_update(self, event):
        """Handle order updates from the group"""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order': event['order'],
            'action': event['action'],
            'station': self.station
        }))
    
    async def order_status_change(self, event):
        """Handle order status changes"""
        await self.send(text_data=json.dumps({
            'type': 'status_change',
            'order_id': event['order_id'],
            'old_status': event['old_status'],
            'new_status': event['new_status'],
            'station': self.station
        }))
    
    @database_sync_to_async
    def get_orders_for_station(self):
        """Get orders for the current station"""
        orders = Transaction.objects.filter(status=self.station).order_by('date_ordered')[:20]
        return [
            {
                'id': order.id,
                'ref_code': order.ref_code,
                'customer_name': order.customer_name or order.owner.user.username,
                'date_ordered': order.date_ordered.isoformat(),
                'status': order.status,
                'items': [
                    {
                        'name': item.name,
                        'ticket': item.ticket,
                        'value': float(item.value)
                    }
                    for item in order.items.all()
                ],
                'total_tickets': order.get_total_tickets(),
                'total_value': float(order.get_total_value()),
                'item_count': order.items.count()
            }
            for order in orders
        ]
