#!/usr/bin/env python3
"""
Test WebSocket connections through nginx proxy (production setup)
"""
import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_proxy():
    """Test WebSocket connections through nginx proxy"""
    print("🔍 Testing WebSocket Connections Through Nginx Proxy")
    print("=" * 60)
    
    base_url = "ws://localhost:3000/ws"  # Through nginx proxy
    
    endpoints = [
        "/kitchen/display",
        "/orders/updates", 
        "/admin/dashboard"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\n🧪 Testing: {endpoint}")
        print(f"   URL: {url}")
        
        try:
            async with websockets.connect(url) as websocket:
                print(f"   ✅ Connected successfully")
                
                # Send a ping message
                ping_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
                await websocket.send(json.dumps(ping_message))
                print(f"   📤 Sent ping message")
                
                # Wait for pong response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    print(f"   📥 Received response: {response_data.get('type', 'unknown')}")
                    results[endpoint] = "✅ PASS"
                except asyncio.TimeoutError:
                    print(f"   ⏰ Timeout waiting for response")
                    results[endpoint] = "⚠️  TIMEOUT"
                except Exception as e:
                    print(f"   ❌ Error receiving response: {e}")
                    results[endpoint] = "❌ FAIL"
                    
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            results[endpoint] = "❌ FAIL"
    
    print(f"\n📊 Test Results:")
    print("=" * 30)
    for endpoint, result in results.items():
        print(f"{endpoint}: {result}")
    
    # Summary
    passed = sum(1 for r in results.values() if r == "✅ PASS")
    total = len(results)
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All WebSocket proxy tests passed!")
        print("\n📱 Your OlgFeast application is ready!")
        print("   Frontend: http://localhost:3000")
        print("   Backend: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("\n🔑 Login credentials:")
        print("   Check deployment_credentials.txt for admin and customer passwords")
    else:
        print("⚠️  Some WebSocket tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(test_websocket_proxy())
    exit(0 if success else 1)
