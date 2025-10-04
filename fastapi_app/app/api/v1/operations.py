from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models.order import Order, OrderStatus
from ...models.user import User
from ...schemas.order import Order as OrderSchema, OrderSummary
from ...api.deps import get_current_staff_user

router = APIRouter()


@router.get("/orders", response_model=List[OrderSchema])
def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get all orders for operations management (staff only)"""
    orders = db.query(Order).order_by(Order.date_ordered.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/orders/pending", response_model=List[OrderSchema])
def get_pending_orders(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get all pending orders (staff only)"""
    orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).order_by(Order.date_ordered).all()
    return orders


@router.get("/orders/preparing", response_model=List[OrderSchema])
def get_preparing_orders(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get all orders being prepared (staff only)"""
    orders = db.query(Order).filter(Order.status == OrderStatus.PREPARING).order_by(Order.date_ordered).all()
    return orders


@router.get("/orders/ready", response_model=List[OrderSchema])
def get_ready_orders(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get all ready orders (staff only)"""
    orders = db.query(Order).filter(Order.status == OrderStatus.READY).order_by(Order.date_ordered).all()
    return orders


@router.get("/orders/completed", response_model=List[OrderSummary])
def get_completed_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get recent completed orders (staff only)"""
    orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETE).order_by(
        Order.date_complete.desc()
    ).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        total_value = sum(item.food_item.value * item.quantity for item in order.order_items)
        total_tickets = sum(item.food_item.ticket * item.quantity for item in order.order_items)
        
        result.append(OrderSummary(
            id=order.id,
            ref_code=order.ref_code,
            customer_name=order.customer_name,
            status=order.status.value,
            total_value=total_value,
            total_tickets=total_tickets,
            item_count=len(order.order_items),
            date_ordered=order.date_ordered
        ))
    
    return result


@router.get("/dashboard/analytics")
def get_operations_analytics(
    current_user: User = Depends(get_current_staff_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for operations dashboard (staff only)"""
    from sqlalchemy import func
    
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Order counts by status
    pending_count = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    preparing_count = db.query(Order).filter(Order.status == OrderStatus.PREPARING).count()
    ready_count = db.query(Order).filter(Order.status == OrderStatus.READY).count()
    
    # Recent activity
    orders_today = db.query(Order).filter(Order.date_ordered >= last_24h).count()
    orders_this_week = db.query(Order).filter(Order.date_ordered >= last_7d).count()
    orders_this_month = db.query(Order).filter(Order.date_ordered >= last_30d).count()
    
    # Timing analytics for completed orders
    completed_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETE)
    
    avg_times = {
        'avg_time_to_preparing': 0,
        'avg_time_to_ready': 0,
        'avg_time_to_complete': 0,
        'avg_total_time': 0
    }
    
    if completed_orders.count() > 0:
        times_to_preparing = []
        times_to_ready = []
        times_to_complete = []
        total_times = []
        
        for order in completed_orders:
            if order.date_preparing:
                time_to_preparing = (order.date_preparing - order.date_ordered).total_seconds() / 60
                times_to_preparing.append(time_to_preparing)
            
            if order.date_ready and order.date_preparing:
                time_to_ready = (order.date_ready - order.date_preparing).total_seconds() / 60
                times_to_ready.append(time_to_ready)
            
            if order.date_complete and order.date_ready:
                time_to_complete = (order.date_complete - order.date_ready).total_seconds() / 60
                times_to_complete.append(time_to_complete)
            
            if order.date_complete:
                total_time = (order.date_complete - order.date_ordered).total_seconds() / 60
                total_times.append(total_time)
        
        avg_times = {
            'avg_time_to_preparing': round(sum(times_to_preparing) / len(times_to_preparing), 2) if times_to_preparing else 0,
            'avg_time_to_ready': round(sum(times_to_ready) / len(times_to_ready), 2) if times_to_ready else 0,
            'avg_time_to_complete': round(sum(times_to_complete) / len(times_to_complete), 2) if times_to_complete else 0,
            'avg_total_time': round(sum(total_times) / len(total_times), 2) if total_times else 0
        }
    
    # Hourly activity for today
    hourly_activity = []
    for hour in range(24):
        hour_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        if hour_start <= now:
            orders_in_hour = db.query(Order).filter(
                Order.date_ordered >= hour_start,
                Order.date_ordered < hour_end
            ).count()
            hourly_activity.append({'hour': hour, 'orders': orders_in_hour})
    
    return {
        'current_status_counts': {
            'pending': pending_count,
            'preparing': preparing_count,
            'ready': ready_count
        },
        'activity_stats': {
            'orders_today': orders_today,
            'orders_this_week': orders_this_week,
            'orders_this_month': orders_this_month
        },
        'timing_analytics': avg_times,
        'hourly_activity': hourly_activity,
        'total_completed_orders': completed_orders.count()
    }
