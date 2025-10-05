from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import secrets
import string
import asyncio
import logging

from ..models.order import Order, OrderItem, OrderStatus
from ..models.cart import Cart, CartItem
from ..schemas.order import OrderCreate, OrderUpdate
from ..websocket.websocket_service import WebSocketService

logger = logging.getLogger(__name__)


class OrderService:
    """Service class for managing orders and related operations."""
    
    def __init__(self, db: Session):
        """Initialize OrderService with database session."""
        self.db = db
        self.websocket_service = WebSocketService(db)
    
    def _generate_ref_code(self) -> str:
        """Generate a unique reference code for orders.
        
        Returns:
            str: A 16-character random string using lowercase letters and digits.
        """
        chars = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(16))
    
    def _ensure_unique_ref_code(self) -> str:
        """Generate a unique reference code that doesn't exist in the database.
        
        Returns:
            str: A unique reference code.
        """
        ref_code = self._generate_ref_code()
        while self.db.query(Order).filter(Order.ref_code == ref_code).first():
            ref_code = self._generate_ref_code()
        return ref_code
    
    def _get_next_display_id(self) -> int:
        """Get the next available display ID (1-999, recycling when needed).
        
        Returns:
            int: The next available display ID.
        """
        # Get the highest display_id currently in use
        max_display_id = self.db.query(Order.display_id).order_by(Order.display_id.desc()).first()
        
        if max_display_id is None:
            # No orders yet, start with 1
            return 1
        
        current_max = max_display_id[0]
        
        # If we're at 999, start recycling from 1
        if current_max >= 999:
            # Find the first gap in the sequence, starting from 1
            for i in range(1, 1000):
                existing = self.db.query(Order).filter(Order.display_id == i).first()
                if existing is None:
                    return i
            
            # If no gaps found (very unlikely), return 1 and let the unique constraint handle it
            return 1
        
        # Return the next number in sequence
        return current_max + 1
    
    async def _broadcast_async(self, coro) -> None:
        """Handle async broadcasting in both sync and async contexts."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the broadcast
                asyncio.create_task(coro)
            else:
                # If we're in a sync context, run the broadcast
                loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
    
    def create_order(self, user_id: int, order_data: OrderCreate) -> Optional[Order]:
        """Create a new order from cart items.
        
        Args:
            user_id: ID of the user creating the order.
            order_data: Order creation data containing customer name.
            
        Returns:
            Order: The created order, or None if cart is empty.
        """
        try:
            # Check if user has items in cart
            cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart or not cart.items:
                logger.warning(f"User {user_id} attempted to create order with empty cart")
                return None
            
            # Generate unique reference code and display ID
            ref_code = self._ensure_unique_ref_code()
            display_id = self._get_next_display_id()
            
            # Create order
            order = Order(
                display_id=display_id,
                ref_code=ref_code,
                user_id=user_id,
                customer_name=order_data.customer_name,
                status=OrderStatus.PENDING
            )
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            
            # Add cart items to order
            self._add_cart_items_to_order(order.id, cart.items)
            
            # Clear the cart
            self._clear_user_cart(cart.id)
            
            self.db.commit()
            self.db.refresh(order)
            
            # Broadcast new order
            asyncio.run(self._broadcast_async(
                self.websocket_service.broadcast_new_order(order)
            ))
            
            logger.info(f"Order #{order.display_id} ({order.ref_code}) created successfully for user {user_id}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create order for user {user_id}: {e}")
            return None
    
    def _add_cart_items_to_order(self, order_id: int, cart_items: List[CartItem]) -> None:
        """Add cart items to an order.
        
        Args:
            order_id: ID of the order to add items to.
            cart_items: List of cart items to add.
        """
        for cart_item in cart_items:
            # Create one order item with the correct quantity
            order_item = OrderItem(
                order_id=order_id,
                food_item_id=cart_item.food_item_id,
                quantity=cart_item.quantity
            )
            self.db.add(order_item)
    
    def _clear_user_cart(self, cart_id: int) -> None:
        """Clear all items from a user's cart.
        
        Args:
            cart_id: ID of the cart to clear.
        """
        self.db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    
    def get_user_orders(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get orders for a specific user.
        
        Args:
            user_id: ID of the user to get orders for.
            skip: Number of orders to skip for pagination.
            limit: Maximum number of orders to return.
            
        Returns:
            List[Order]: List of orders for the user, ordered by date (newest first).
        """
        return self.db.query(Order).filter(Order.user_id == user_id).order_by(
            Order.date_ordered.desc()
        ).offset(skip).limit(limit).all()
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """Get a specific order by ID.
        
        Args:
            order_id: ID of the order to retrieve.
            
        Returns:
            Order: The order if found, None otherwise.
        """
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_user_order(self, user_id: int, order_id: int) -> Optional[Order]:
        """Get a specific order by user ID and order ID.
        
        Args:
            user_id: ID of the user who owns the order.
            order_id: ID of the order to retrieve.
            
        Returns:
            Order: The order if found and belongs to the user, None otherwise.
        """
        return self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
    
    def get_orders(
        self, 
        skip: int = 0, 
        limit: int = 50, 
        status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """Get all orders with optional status filter.
        
        Args:
            skip: Number of orders to skip for pagination.
            limit: Maximum number of orders to return.
            status: Optional status filter.
            
        Returns:
            List[Order]: List of orders matching the criteria, ordered by date (newest first).
        """
        query = self.db.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        
        return query.order_by(Order.date_ordered.desc()).offset(skip).limit(limit).all()
    
    def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        """Update order status with timing fields and broadcast changes.
        
        Args:
            order_id: ID of the order to update.
            new_status: The new status to set.
            
        Returns:
            Order: The updated order if found, None otherwise.
        """
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.warning(f"Attempted to update non-existent order {order_id}")
                return None
            
            old_status = order.status
            order.status = new_status
            
            # Update timing fields based on status
            self._update_order_timing(order, old_status, new_status)
            
            self.db.commit()
            self.db.refresh(order)
            
            # Broadcast status change
            asyncio.run(self._broadcast_async(
                self.websocket_service.broadcast_order_status_change(order, old_status, new_status)
            ))
            
            logger.info(f"Order #{order.display_id} ({order.ref_code}) status updated: {old_status.value} → {new_status.value}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update order {order_id} status: {e}")
            return None
    
    def _update_order_timing(self, order: Order, old_status: OrderStatus, new_status: OrderStatus) -> None:
        """Update timing fields based on status transitions.
        
        Args:
            order: The order to update.
            old_status: Previous status.
            new_status: New status.
        """
        now = datetime.utcnow()
        if new_status == OrderStatus.PREPARING and old_status == OrderStatus.PENDING:
            order.date_preparing = now
        elif new_status == OrderStatus.READY and old_status == OrderStatus.PREPARING:
            order.date_ready = now
        elif new_status == OrderStatus.COMPLETE and old_status == OrderStatus.READY:
            order.date_complete = now
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get all orders with a specific status.
        
        Args:
            status: The status to filter by.
            
        Returns:
            List[Order]: List of orders with the specified status, ordered by date (oldest first).
        """
        return self.db.query(Order).filter(Order.status == status).order_by(
            Order.date_ordered
        ).all()
    
    def get_order_analytics(self) -> Dict[str, Any]:
        """Get comprehensive order analytics.
        
        Returns:
            Dict[str, Any]: Dictionary containing various analytics metrics.
        """
        try:
            now = datetime.utcnow()
            time_ranges = self._get_time_ranges(now)
            
            # Basic statistics
            basic_stats = self._get_basic_order_stats(time_ranges)
            
            # Status counts
            status_counts = self._get_status_counts()
            
            # Revenue calculations
            revenue_stats = self._get_revenue_stats(time_ranges)
            
            # Timing analytics
            timing_stats = self._get_timing_analytics()
            
            return {
                'total_orders': basic_stats['total_orders'],
                'orders_today': basic_stats['orders_today'],
                'orders_this_week': basic_stats['orders_this_week'],
                'orders_this_month': basic_stats['orders_this_month'],
                'status_counts': status_counts,
                'current_status_counts': {
                    'pending': status_counts.get('pending', 0),
                    'preparing': status_counts.get('preparing', 0),
                    'ready': status_counts.get('ready', 0),
                    'complete': status_counts.get('complete', 0)
                },
                'activity_stats': {
                    'orders_today': basic_stats['orders_today'],
                    'orders_this_week': basic_stats['orders_this_week'],
                    'orders_this_month': basic_stats['orders_this_month']
                },
                'total_completed_orders': status_counts.get('complete', 0),
                'timing_analytics': timing_stats,
                'total_revenue': revenue_stats['total_revenue'],
                'revenue_today': revenue_stats['revenue_today'],
                'revenue_this_week': revenue_stats['revenue_this_week']
            }
            
        except Exception as e:
            logger.error(f"Failed to get order analytics: {e}")
            return self._get_default_analytics()
    
    def _get_time_ranges(self, now: datetime) -> Dict[str, datetime]:
        """Get time ranges for analytics calculations."""
        return {
            'last_24h': now - timedelta(hours=24),
            'last_7d': now - timedelta(days=7),
            'last_30d': now - timedelta(days=30)
        }
    
    def _get_basic_order_stats(self, time_ranges: Dict[str, datetime]) -> Dict[str, int]:
        """Get basic order statistics."""
        return {
            'total_orders': self.db.query(Order).count(),
            'orders_today': self.db.query(Order).filter(
                Order.date_ordered >= time_ranges['last_24h']
            ).count(),
            'orders_this_week': self.db.query(Order).filter(
                Order.date_ordered >= time_ranges['last_7d']
            ).count(),
            'orders_this_month': self.db.query(Order).filter(
                Order.date_ordered >= time_ranges['last_30d']
            ).count()
        }
    
    def _get_status_counts(self) -> Dict[str, int]:
        """Get counts of orders by status."""
        status_counts = {}
        for status in OrderStatus:
            count = self.db.query(Order).filter(Order.status == status).count()
            status_counts[status.value] = count
        return status_counts
    
    def _get_revenue_stats(self, time_ranges: Dict[str, datetime]) -> Dict[str, float]:
        """Get revenue statistics."""
        completed_orders = self.db.query(Order).filter(Order.status == OrderStatus.COMPLETE)
        
        total_revenue = 0
        revenue_today = 0
        revenue_this_week = 0
        
        for order in completed_orders:
            order_value = sum(item.food_item.value * item.quantity for item in order.order_items)
            total_revenue += order_value
            
            if order.date_ordered >= time_ranges['last_24h']:
                revenue_today += order_value
            if order.date_ordered >= time_ranges['last_7d']:
                revenue_this_week += order_value
        
        return {
            'total_revenue': round(total_revenue, 2),
            'revenue_today': round(revenue_today, 2),
            'revenue_this_week': round(revenue_this_week, 2)
        }
    
    def _get_timing_analytics(self) -> Dict[str, float]:
        """Get timing analytics for completed orders."""
        completed_orders = self.db.query(Order).filter(Order.status == OrderStatus.COMPLETE)
        
        if completed_orders.count() == 0:
            return {'avg_total_time': 0}
        
        total_time = 0
        for order in completed_orders:
            if order.date_complete and order.date_ordered:
                time_diff = (order.date_complete - order.date_ordered).total_seconds() / 60  # minutes
                total_time += time_diff
        
        return {
            'avg_total_time': round(total_time / completed_orders.count(), 1)
        }
    
    def _get_default_analytics(self) -> Dict[str, Any]:
        """Get default analytics when calculation fails."""
        return {
            'total_orders': 0,
            'orders_today': 0,
            'orders_this_week': 0,
            'orders_this_month': 0,
            'status_counts': {},
            'current_status_counts': {
                'pending': 0,
                'preparing': 0,
                'ready': 0,
                'complete': 0
            },
            'activity_stats': {
                'orders_today': 0,
                'orders_this_week': 0,
                'orders_this_month': 0
            },
            'total_completed_orders': 0,
            'timing_analytics': {'avg_total_time': 0},
            'total_revenue': 0,
            'revenue_today': 0,
            'revenue_this_week': 0
        }
