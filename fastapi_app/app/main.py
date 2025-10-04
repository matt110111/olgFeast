from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
from datetime import datetime

from .core.config import settings
from .api.v1.auth import router as auth_router
from .api.v1.menu import router as menu_router
from .api.v1.cart import router as cart_router
from .api.v1.orders import router as orders_router
from .api.v1.operations import router as operations_router
from .core.database import engine, Base
from .websocket.connection_manager import manager
from .websocket.websocket_endpoints import (
    send_kitchen_state_update,
    send_user_orders_update,
    send_dashboard_analytics,
    send_all_orders_update
)

# Import models to register them with SQLAlchemy
from .models import user, menu, cart, order

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Modern restaurant order management system with real-time updates",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    menu_router,
    prefix="/api/v1/menu",
    tags=["menu"]
)

app.include_router(
    cart_router,
    prefix="/api/v1/cart",
    tags=["shopping-cart"]
)

app.include_router(
    orders_router,
    prefix="/api/v1/orders",
    tags=["orders"]
)

app.include_router(
    operations_router,
    prefix="/api/v1/operations",
    tags=["operations"]
)

# WebSocket endpoints
@app.websocket("/ws/kitchen/display")
async def kitchen_display_ws(websocket: WebSocket):
    """WebSocket endpoint for kitchen display updates"""
    try:
        await manager.connect(websocket, "kitchen_display")
        
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
    except Exception as e:
        print(f"❌ WebSocket error in kitchen display: {e}")
        await manager.disconnect(websocket)


@app.websocket("/ws/orders/updates")
async def order_updates_ws(websocket: WebSocket):
    """WebSocket endpoint for order status updates"""
    await manager.connect(websocket, "order_updates")
    
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


@app.websocket("/ws/admin/dashboard")
async def admin_dashboard_ws(websocket: WebSocket):
    """WebSocket endpoint for admin dashboard updates"""
    try:
        await manager.connect(websocket, "admin_dashboard")
        
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
    except Exception as e:
        print(f"❌ WebSocket error in admin dashboard: {e}")
        await manager.disconnect(websocket)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to olgFeast API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.APP_VERSION}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
