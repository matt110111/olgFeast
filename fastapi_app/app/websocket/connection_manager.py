"""
WebSocket connection manager for handling multiple connections
"""
from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Active connections by channel
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "kitchen_display": set(),
            "order_updates": set(),
            "admin_dashboard": set(),
        }
        # Connection metadata
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, channel: str, user_info: dict = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Add to appropriate channel
        if channel in self.active_connections:
            self.active_connections[channel].add(websocket)
        
        # Store connection metadata
        self.connection_info[websocket] = {
            "channel": channel,
            "connected_at": datetime.utcnow(),
            "user_info": user_info or {},
        }
        
        print(f"✅ WebSocket connected to channel: {channel}")
        
        # Send initial data based on channel
        await self._send_initial_data(websocket, channel)
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        # Remove from all channels
        for channel_connections in self.active_connections.values():
            channel_connections.discard(websocket)
        
        # Remove metadata
        if websocket in self.connection_info:
            channel = self.connection_info[websocket].get("channel", "unknown")
            del self.connection_info[websocket]
            print(f"❌ WebSocket disconnected from channel: {channel}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"❌ Error sending personal message: {e}")
            await self.disconnect(websocket)
    
    async def send_json_message(self, data: dict, websocket: WebSocket):
        """Send a JSON message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(data, default=str))
        except Exception as e:
            print(f"❌ Error sending JSON message: {e}")
            await self.disconnect(websocket)
    
    async def broadcast_to_channel(self, message: str, channel: str):
        """Broadcast a message to all connections in a specific channel"""
        if channel not in self.active_connections:
            return
        
        # Create a list of connections to avoid modification during iteration
        connections_to_remove = []
        
        for websocket in self.active_connections[channel].copy():
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"❌ Error broadcasting to {channel}: {e}")
                connections_to_remove.append(websocket)
        
        # Remove failed connections
        for websocket in connections_to_remove:
            await self.disconnect(websocket)
    
    async def broadcast_json_to_channel(self, data: dict, channel: str):
        """Broadcast a JSON message to all connections in a specific channel"""
        message = json.dumps(data, default=str)
        await self.broadcast_to_channel(message, channel)
    
    async def broadcast_to_all_channels(self, message: str):
        """Broadcast a message to all active connections"""
        for channel in self.active_connections:
            await self.broadcast_to_channel(message, channel)
    
    async def _send_initial_data(self, websocket: WebSocket, channel: str):
        """Send initial data when a connection is established"""
        if channel == "kitchen_display":
            # Send current kitchen state
            await self.send_kitchen_state(websocket)
        elif channel == "admin_dashboard":
            # Send dashboard analytics
            await self.send_dashboard_data(websocket)
    
    async def send_kitchen_state(self, websocket: WebSocket):
        """Send current kitchen display state"""
        # This will be implemented with actual data from the database
        initial_data = {
            "type": "kitchen_update",
            "data": {
                "pending_orders": [],
                "preparing_orders": [],
                "ready_orders": []
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_json_message(initial_data, websocket)
    
    async def send_dashboard_data(self, websocket: WebSocket):
        """Send initial dashboard data"""
        initial_data = {
            "type": "dashboard_update",
            "data": {
                "total_orders": 0,
                "orders_today": 0,
                "revenue_today": 0.0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_json_message(initial_data, websocket)
    
    def get_connection_count(self, channel: str = None) -> int:
        """Get the number of active connections"""
        if channel:
            return len(self.active_connections.get(channel, set()))
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connection_info(self) -> dict:
        """Get information about all active connections"""
        return {
            "total_connections": self.get_connection_count(),
            "channel_connections": {
                channel: len(connections) 
                for channel, connections in self.active_connections.items()
            },
            "connections": {
                str(websocket): info 
                for websocket, info in self.connection_info.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()
