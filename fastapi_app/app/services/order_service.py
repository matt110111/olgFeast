from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import string

from ..models.order import Order, OrderItem, OrderStatus
from ..models.cart import Cart, CartItem
from ..schemas.order import OrderCreate, OrderUpdate


class OrderService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_ref_code(self) -> str:
        """Generate a unique reference code for orders"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(16))
    
    def create_order(self, user_id: int, order_data: OrderCreate) -> Optional[Order]:
        """Create a new order from cart items"""
        # Check if user has items in cart
        cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart or not cart.items:
            return None
        
        # Generate unique reference code
        ref_code = self.generate_ref_code()
        while self.db.query(Order).filter(Order.ref_code == ref_code).first():
            ref_code = self.generate_ref_code()
        
        # Create order
        order = Order(
            ref_code=ref_code,
            user_id=user_id,
            customer_name=order_data.customer_name,
            status=OrderStatus.PENDING
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        # Add cart items to order
        for cart_item in cart.items:
            # Add item multiple times based on quantity
            for _ in range(cart_item.quantity):
                order_item = OrderItem(
                    order_id=order.id,
                    food_item_id=cart_item.food_item_id,
                    quantity=1
                )
                self.db.add(order_item)
        
        # Clear the cart
        self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def get_user_orders(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get orders for a specific user"""
        return self.db.query(Order).filter(Order.user_id == user_id).order_by(
            Order.date_ordered.desc()
        ).offset(skip).limit(limit).all()
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """Get a specific order by ID"""
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_user_order(self, user_id: int, order_id: int) -> Optional[Order]:
        """Get a specific order by user ID and order ID"""
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
        """Get all orders with optional status filter"""
        query = self.db.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        
        return query.order_by(Order.date_ordered.desc()).offset(skip).limit(limit).all()
    
    def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        """Update order status with timing fields"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        
        old_status = order.status
        order.status = new_status
        
        # Update timing fields based on status
        now = datetime.utcnow()
        if new_status == OrderStatus.PREPARING and old_status == OrderStatus.PENDING:
            order.date_preparing = now
        elif new_status == OrderStatus.READY and old_status == OrderStatus.PREPARING:
            order.date_ready = now
        elif new_status == OrderStatus.COMPLETE and old_status == OrderStatus.READY:
            order.date_complete = now
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get all orders with a specific status"""
        return self.db.query(Order).filter(Order.status == status).order_by(
            Order.date_ordered
        ).all()
    
    def get_order_analytics(self) -> dict:
        """Get comprehensive order analytics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Basic statistics
        total_orders = self.db.query(Order).count()
        orders_today = self.db.query(Order).filter(Order.date_ordered >= last_24h).count()
        orders_this_week = self.db.query(Order).filter(Order.date_ordered >= last_7d).count()
        orders_this_month = self.db.query(Order).filter(Order.date_ordered >= last_30d).count()
        
        # Status counts
        status_counts = {}
        for status in OrderStatus:
            count = self.db.query(Order).filter(Order.status == status).count()
            status_counts[status.value] = count
        
        # Revenue calculations
        completed_orders = self.db.query(Order).filter(Order.status == OrderStatus.COMPLETE)
        
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
        
        return {
            'total_orders': total_orders,
            'orders_today': orders_today,
            'orders_this_week': orders_this_week,
            'orders_this_month': orders_this_month,
            'status_counts': status_counts,
            'total_revenue': round(total_revenue, 2),
            'revenue_today': round(revenue_today, 2),
            'revenue_this_week': round(revenue_this_week, 2)
        }
