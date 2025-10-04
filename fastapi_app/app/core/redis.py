"""
Redis connection and configuration for WebSocket broadcasting
"""
import aioredis
from .config import settings


class RedisManager:
    """Redis connection manager for WebSocket broadcasting"""
    
    def __init__(self):
        self.redis_client = None
        self.pubsub = None
    
    async def connect(self):
        """Connect to Redis server"""
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            print("✅ Connected to Redis for WebSocket broadcasting")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis server"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def publish(self, channel: str, message: dict):
        """Publish message to Redis channel"""
        if self.redis_client:
            await self.redis_client.publish(channel, str(message))
    
    async def subscribe(self, channel: str):
        """Subscribe to Redis channel"""
        if self.pubsub:
            await self.pubsub.subscribe(channel)
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from Redis channel"""
        if self.pubsub:
            await self.pubsub.unsubscribe(channel)
    
    async def get_message(self):
        """Get message from subscribed channels"""
        if self.pubsub:
            return await self.pubsub.get_message(ignore_subscribe_messages=True)
        return None


# Global Redis manager instance
redis_manager = RedisManager()
