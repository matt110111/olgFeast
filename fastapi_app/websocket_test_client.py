#!/usr/bin/env python3
"""
Simple WebSocket test client for testing real-time functionality
"""
import asyncio
import websockets
import json
from datetime import datetime


async def test_kitchen_display():
    """Test kitchen display WebSocket"""
    print("🔌 Connecting to kitchen display WebSocket...")
    
    try:
        async with websockets.connect("ws://localhost:8000/ws/kitchen/display") as websocket:
            print("✅ Connected to kitchen display!")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Sent ping")
            
            # Listen for messages
            for i in range(10):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📥 Received: {data['type']} at {datetime.now().strftime('%H:%M:%S')}")
                    
                    if data['type'] == 'kitchen_update':
                        pending = len(data['data']['pending_orders'])
                        preparing = len(data['data']['preparing_orders'])
                        ready = len(data['data']['ready_orders'])
                        print(f"   📊 Kitchen Status: {pending} pending, {preparing} preparing, {ready} ready")
                
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {message}")
                    break
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_order_updates():
    """Test order updates WebSocket"""
    print("\n🔌 Connecting to order updates WebSocket...")
    
    try:
        async with websockets.connect("ws://localhost:8000/ws/orders/updates") as websocket:
            print("✅ Connected to order updates!")
            
            # Subscribe to user orders
            await websocket.send(json.dumps({
                "type": "subscribe_orders",
                "user_id": 4  # customer user ID
            }))
            print("📤 Subscribed to user orders")
            
            # Listen for messages
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📥 Received: {data['type']} at {datetime.now().strftime('%H:%M:%S')}")
                
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {message}")
                    break
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_admin_dashboard():
    """Test admin dashboard WebSocket"""
    print("\n🔌 Connecting to admin dashboard WebSocket...")
    
    # You would need a valid admin token here
    token = "your-admin-token-here"
    
    try:
        async with websockets.connect(f"ws://localhost:8000/ws/admin/dashboard?token={token}") as websocket:
            print("✅ Connected to admin dashboard!")
            
            # Request analytics
            await websocket.send(json.dumps({"type": "request_analytics"}))
            print("📤 Requested analytics")
            
            # Listen for messages
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📥 Received: {data['type']} at {datetime.now().strftime('%H:%M:%S')}")
                
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {message}")
                    break
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all WebSocket tests"""
    print("🚀 Starting WebSocket Tests")
    print("=" * 50)
    
    # Test kitchen display
    await test_kitchen_display()
    
    # Test order updates
    await test_order_updates()
    
    # Test admin dashboard (will fail without valid token)
    # await test_admin_dashboard()
    
    print("\n✅ WebSocket tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
