from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
from datetime import datetime, timezone
import asyncio
from sqlalchemy import text
from sqlalchemy.orm import Session
from .core.database import get_db
from .api.deps import user_for_token
from .core.security import verify_token

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
from .models import user, menu, cart, order, event
from .api.v1.events import router as events_router

# Create database tables


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

app.include_router(events_router, prefix="/api/v1/events", tags=["events"])


async def event_socket(websocket: WebSocket, channel: str, db: Session):
    origin = websocket.headers.get("origin")
    if origin and settings.ALLOWED_HOSTS != ["*"] and origin not in settings.ALLOWED_HOSTS:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        auth = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        token = auth.get("token", "")
        user = user_for_token(token, db)
        if not user or (channel != "order_updates" and not user.is_staff) or (channel == "admin_dashboard" and not user.is_admin):
            await websocket.close(code=1008)
            return
        user_id = user.id
        payload = verify_token(token)
        db.rollback()
        await manager.connect(websocket, channel, {"user_id": user_id})
        await manager.send_json_message({"type": "authenticated"}, websocket)
        while True:
            remaining = payload["exp"] - datetime.now(timezone.utc).timestamp()
            if remaining <= 0:
                await websocket.close(code=4001)
                return
            message = await asyncio.wait_for(websocket.receive_json(), timeout=min(remaining, 65))
            db.expire_all()
            active_user = user_for_token(token, db)
            if not active_user or (channel != "order_updates" and not active_user.is_staff) or (channel == "admin_dashboard" and not active_user.is_admin):
                await websocket.close(code=4001)
                return
            db.rollback()
            kind = message.get("type")
            if kind == "ping":
                await manager.send_json_message({"type": "pong"}, websocket)
            elif channel == "kitchen_display" and kind == "request_update":
                await send_kitchen_state_update(websocket)
            elif channel == "admin_dashboard" and kind == "request_analytics":
                await send_dashboard_analytics(websocket)
            elif channel == "admin_dashboard" and kind == "request_orders":
                await send_all_orders_update(websocket)
            elif channel == "order_updates" and kind == "subscribe_orders":
                # A client can only subscribe to its own orders.
                await send_user_orders_update(websocket, user_id)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except (ValueError, TypeError, AttributeError):
        await websocket.close(code=1008)
    finally:
        await manager.disconnect(websocket)


@app.websocket("/ws/kitchen/display")
async def kitchen_display_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await event_socket(websocket, "kitchen_display", db)


@app.websocket("/ws/orders/updates")
async def order_updates_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await event_socket(websocket, "order_updates", db)


@app.websocket("/ws/admin/dashboard")
async def admin_dashboard_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await event_socket(websocket, "admin_dashboard", db)

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
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        db.execute(text("SELECT 1"))
        revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if revision != "0005":
            raise RuntimeError("Migration required")
    except Exception:
        raise HTTPException(503, "Database not ready")
    return {"status": "healthy", "version": settings.APP_VERSION}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
