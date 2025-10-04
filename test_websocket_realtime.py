#!/usr/bin/env python3
"""
Test script to verify real-time WebSocket updates
"""
import asyncio
import websockets
import json
import requests
import time

async def test_realtime_updates():
    """Test real-time WebSocket updates by creating an order and watching for updates"""
    
    print("🚀 Testing Real-Time WebSocket Updates")
    print("=" * 50)
    
    # Step 1: Login as customer and create an order
    print("1️⃣ Logging in as customer...")
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        data={"username": "customer", "password": "customer123"}
    )
    
    if login_response.status_code != 200:
        print("❌ Customer login failed")
        return
    
    customer_token = login_response.json()["access_token"]
    print("✅ Customer logged in")
    
    # Step 2: Add items to cart
    print("2️⃣ Adding items to cart...")
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # Add some items to cart
    cart_items = [
        {"food_item_id": 1, "quantity": 2},  # Buffalo Wings
        {"food_item_id": 2, "quantity": 1},  # Mozzarella Sticks
    ]
    
    for item in cart_items:
        response = requests.post(
            "http://localhost:8000/api/v1/cart/items",
            json=item,
            headers=headers
        )
        if response.status_code == 200:
            print(f"✅ Added {item['quantity']}x item {item['food_item_id']} to cart")
    
    # Step 3: Connect to WebSocket as admin
    print("3️⃣ Connecting to admin dashboard WebSocket...")
    
    async def websocket_listener():
        uri = 'ws://localhost:8000/ws/admin/dashboard'
        try:
            async with websockets.connect(uri) as websocket:
                print("✅ Connected to admin dashboard WebSocket")
                
                # Request initial data
                await websocket.send(json.dumps({"type": "request_analytics"}))
                await websocket.send(json.dumps({"type": "request_orders"}))
                
                # Listen for updates
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        print(f"📨 WebSocket message: {data['type']}")
                        
                        if data['type'] == 'new_order':
                            print("🎉 NEW ORDER DETECTED!")
                            print(f"   Order: {data['data']['ref_code']}")
                            print(f"   Customer: {data['data']['customer_name']}")
                            print(f"   Total: ${data['data']['total_value']}")
                            return True
                            
                    except asyncio.TimeoutError:
                        continue
                        
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            return False
    
    # Step 4: Create order while listening to WebSocket
    print("4️⃣ Creating order...")
    
    # Start WebSocket listener
    listener_task = asyncio.create_task(websocket_listener())
    
    # Wait a moment for WebSocket to connect
    await asyncio.sleep(2)
    
    # Create the order
    order_response = requests.post(
        "http://localhost:8000/api/v1/orders/checkout",
        json={"customer_name": "WebSocket Test Customer"},
        headers=headers
    )
    
    if order_response.status_code == 200:
        order = order_response.json()
        print(f"✅ Order created: {order['ref_code']}")
        print(f"   Customer: {order['customer_name']}")
        print(f"   Status: {order['status']}")
    else:
        print(f"❌ Order creation failed: {order_response.text}")
        listener_task.cancel()
        return
    
    # Step 5: Wait for WebSocket update
    print("5️⃣ Waiting for WebSocket update...")
    try:
        result = await asyncio.wait_for(listener_task, timeout=10)
        if result:
            print("✅ REAL-TIME UPDATE CONFIRMED!")
            print("🎯 WebSocket system is working perfectly!")
        else:
            print("❌ No WebSocket update received")
    except asyncio.TimeoutError:
        print("⏰ Timeout waiting for WebSocket update")
        listener_task.cancel()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_realtime_updates())
