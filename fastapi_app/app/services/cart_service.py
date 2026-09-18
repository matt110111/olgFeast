from sqlalchemy.orm import Session
from typing import Optional
from ..models.cart import Cart, CartItem
from ..models.menu import FoodItem
from ..schemas.cart import CartItemCreate, CartItemUpdate, CartSummary


class CartService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_cart(self, user_id: int) -> Cart:
        """Get existing cart or create new one for user"""
        cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        return cart
    
    def get_cart_summary(self, user_id: int) -> CartSummary:
        """Get cart summary with totals"""
        cart = self.get_or_create_cart(user_id)
        
        total_items = 0
        total_value = 0.0
        total_tickets = 0
        
        for item in cart.items:
            total_items += item.quantity
            total_value += item.food_item.value * item.quantity
            total_tickets += item.food_item.ticket * item.quantity
        
        return CartSummary(
            total_items=total_items,
            total_value=round(total_value, 2),
            total_tickets=total_tickets,
            items=cart.items
        )
    
    def add_item_to_cart(self, user_id: int, item_data: CartItemCreate) -> Optional[CartItem]:
        """Add item to cart or update quantity if already exists"""
        # Verify food item exists
        food_item = self.db.query(FoodItem).filter(FoodItem.id == item_data.food_item_id).first()
        if not food_item:
            return None
        
        cart = self.get_or_create_cart(user_id)
        
        # Check if item already exists in cart
        existing_item = self.db.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.food_item_id == item_data.food_item_id
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += item_data.quantity
            self.db.commit()
            self.db.refresh(existing_item)
            return existing_item
        else:
            # Create new cart item
            cart_item = CartItem(
                cart_id=cart.id,
                food_item_id=item_data.food_item_id,
                quantity=item_data.quantity
            )
            self.db.add(cart_item)
            self.db.commit()
            self.db.refresh(cart_item)
            return cart_item
    
    def update_cart_item(self, user_id: int, item_id: int, item_data: CartItemUpdate) -> Optional[CartItem]:
        """Update cart item quantity"""
        cart = self.get_or_create_cart(user_id)
        
        cart_item = self.db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            return None
        
        cart_item.quantity = item_data.quantity
        self.db.commit()
        self.db.refresh(cart_item)
        return cart_item
    
    def remove_cart_item(self, user_id: int, item_id: int) -> bool:
        """Remove item from cart"""
        cart = self.get_or_create_cart(user_id)
        
        cart_item = self.db.query(CartItem).filter(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            return False
        
        self.db.delete(cart_item)
        self.db.commit()
        return True
    
    def clear_cart(self, user_id: int) -> bool:
        """Clear all items from cart"""
        cart = self.get_or_create_cart(user_id)
        
        # Delete all cart items
        self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        self.db.commit()
        return True
    
    def get_cart_items(self, user_id: int):
        """Get all items in user's cart"""
        cart = self.get_or_create_cart(user_id)
        return cart.items
