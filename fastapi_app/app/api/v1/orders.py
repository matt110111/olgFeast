from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import secrets
import string

from ...core.database import get_db
from ...models.order import Order, OrderItem, OrderStatus
from ...models.cart import Cart, CartItem
from ...models.user import User
from ...schemas.order import Order as OrderSchema, OrderCreate, OrderUpdate, OrderSummary, OrderAnalytics
from ...api.deps import get_current_user, get_current_staff_user
from ...services.order_service import OrderService

router = APIRouter()


def broadcast_new_order_background(message: dict):
    """Background task to broadcast new order messages"""
    import threading
    import asyncio

    def _broadcast():
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def broadcast():
                from ...websocket.connection_manager import manager
                await manager.broadcast_json_to_channel(message, "kitchen_display")
                await manager.broadcast_json_to_channel(message, "admin_dashboard")
                print(f"📢 Broadcasted new order: {message['data']['ref_code']}")

            loop.run_until_complete(broadcast())
            loop.close()
        except Exception as e:
            print(f"⚠️ Failed to broadcast new order: {e}")

    # Run in background thread
    thread = threading.Thread(target=_broadcast)
    thread.daemon = True
    thread.start()


def broadcast_status_change_background(message: dict):
    """Background task to broadcast status change messages"""
    import threading
    import asyncio

    def _broadcast():
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def broadcast():
                from ...websocket.connection_manager import manager
                await manager.broadcast_json_to_channel(message, "kitchen_display")
                await manager.broadcast_json_to_channel(message, "admin_dashboard")
                print(f"📢 Broadcasted status change: {message['data']['ref_code']} {message['data']['old_status']} → {message['data']['new_status']}")

            loop.run_until_complete(broadcast())
            loop.close()
        except Exception as e:
            print(f"⚠️ Failed to broadcast status change: {e}")

    # Run in background thread
    thread = threading.Thread(target=_broadcast)
    thread.daemon = True
    thread.start()


@router.post("/checkout", response_model=OrderSchema)
def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new order from cart items"""
    order_service = OrderService(db)
    order = order_service.create_order(current_user.id, order_data)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty or order creation failed"
        )
    
    return order


@router.get("/my-orders", response_model=List[OrderSummary])
def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's orders"""
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(
        Order.date_ordered.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        total_value = sum(item.food_item.value * item.quantity for item in order.order_items)
        total_tickets = sum(item.food_item.ticket * item.quantity for item in order.order_items)
        
        result.append(OrderSummary(
            id=order.id,
            display_id=order.display_id,
            ref_code=order.ref_code,
            customer_name=order.customer_name,
            status=order.status.value,
            total_value=total_value,
            total_tickets=total_tickets,
            item_count=len(order.order_items),
            date_ordered=order.date_ordered
        ))
    
    return result


@router.get("/my-orders/{order_id}", response_model=OrderSchema)
def get_my_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific order by current user"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.get("/", response_model=List[OrderSchema])
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: OrderStatus = Query(None),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get all orders (staff only)"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.date_ordered.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderSchema)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get a specific order (staff only)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.put("/{order_id}/status", response_model=OrderSchema)
def update_order_status(
    order_id: int,
    order_update: OrderUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Update order status (staff only)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not order_update.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status is required"
        )
    
    # Validate status transition
    valid_statuses = [status.value for status in OrderStatus]
    if order_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    old_status = order.status
    order.status = OrderStatus(order_update.status)
    
    # Update timing fields based on status
    current_time = datetime.utcnow()
    if order.status == OrderStatus.PREPARING and old_status == OrderStatus.PENDING:
        order.date_preparing = current_time
    elif order.status == OrderStatus.READY and old_status == OrderStatus.PREPARING:
        order.date_ready = current_time
    elif order.status == OrderStatus.COMPLETE and old_status == OrderStatus.READY:
        order.date_complete = current_time
    
    db.commit()
    db.refresh(order)
    
    # Schedule WebSocket broadcast for status change
    try:
        # Create status change message
        status_change_message = {
            "type": "order_status_change",
            "data": {
                "order_id": order.id,
                "ref_code": order.ref_code,
                "old_status": old_status.value,
                "new_status": order.status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "customer_name": order.customer_name
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # Schedule background broadcast
        background_tasks.add_task(broadcast_status_change_background, status_change_message)

    except Exception as e:
        print(f"⚠️ Failed to schedule status change broadcast: {e}")
    
    return order


@router.get("/analytics/dashboard", response_model=OrderAnalytics)
def get_order_analytics(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get order analytics for admin dashboard (staff only)"""
    from datetime import timedelta
    from sqlalchemy import func
    
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Basic statistics
    total_orders = db.query(Order).count()
    orders_today = db.query(Order).filter(Order.date_ordered >= last_24h).count()
    orders_this_week = db.query(Order).filter(Order.date_ordered >= last_7d).count()
    orders_this_month = db.query(Order).filter(Order.date_ordered >= last_30d).count()
    
    # Status counts
    status_counts = {}
    for status in OrderStatus:
        count = db.query(Order).filter(Order.status == status).count()
        status_counts[status.value] = count
    
    # Revenue calculations
    completed_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETE)
    
    total_revenue = 0
    revenue_today = 0
    revenue_this_week = 0
    
    for order in completed_orders:
        order_value = sum(item.food_item.value * item.quantity for item in order.order_items)
        total_revenue += order_value
        
        if order.date_ordered >= last_24h:
            revenue_today += order_value
        if order.date_ordered >= last_7d:
            revenue_this_week += order_value
    
    return OrderAnalytics(
        total_orders=total_orders,
        orders_today=orders_today,
        orders_this_week=orders_this_week,
        orders_this_month=orders_this_month,
        status_counts=status_counts,
        total_revenue=round(total_revenue, 2),
        revenue_today=round(revenue_today, 2),
        revenue_this_week=round(revenue_this_week, 2)
    )
