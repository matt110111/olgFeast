#!/usr/bin/env python3
"""
WebSocket Test Script for OlgFeast
Tests WebSocket connections to verify they're working
"""
import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_websocket_connection(url, endpoint_name):
    """Test a WebSocket connection"""
    print(f"\n🔍 Testing {endpoint_name}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"✅ Connected to {url}")
            
            # Send a ping message
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")
            
            # Wait for pong response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📥 Received: {data}")
                
                if data.get("type") == "pong":
                    print("✅ Ping-pong successful!")
                    return True
                else:
                    print(f"❌ Unexpected response type: {data.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for response")
                return False
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_all_websockets():
    """Test all WebSocket endpoints"""
    base_url = "ws://localhost:8000"
    endpoints = [
        ("/ws/kitchen/display", "Kitchen Display"),
        ("/ws/orders/updates", "Order Updates"),
        ("/ws/admin/dashboard", "Admin Dashboard")
    ]
    
    print("🚀 Testing OlgFeast WebSocket Connections")
    print("=" * 50)
    
    results = []
    for endpoint, name in endpoints:
        url = f"{base_url}{endpoint}"
        success = await test_websocket_connection(url, name)
        results.append((name, success))
    
    print("\n📊 Test Results:")
    print("=" * 20)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
        if not success:
            all_passed = False
    
    print(f"\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    print("WebSocket Test for OlgFeast")
    print(f"Testing at: {datetime.now()}")
    
    try:
        result = asyncio.run(test_all_websockets())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
