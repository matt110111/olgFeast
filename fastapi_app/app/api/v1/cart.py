from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.cart import Cart, CartItem
from ...models.menu import FoodItem
from ...models.user import User
from ...schemas.cart import Cart as CartSchema, CartItem as CartItemSchema, CartItemCreate, CartItemUpdate, CartSummary
from ...api.deps import get_current_user

router = APIRouter()


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    """Get existing cart or create new one for user"""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.get("/items", response_model=CartSummary)
def get_cart_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all items in user's cart"""
    cart = get_or_create_cart(db, current_user.id)
    
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


@router.post("/items", response_model=CartItemSchema)
def add_item_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to cart or update quantity if already exists"""
    # Verify food item exists
    food_item = db.query(FoodItem).filter(FoodItem.id == item_data.food_item_id).first()
    if not food_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found"
        )
    
    cart = get_or_create_cart(db, current_user.id)
    
    # Check if item already exists in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.food_item_id == item_data.food_item_id
    ).first()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += item_data.quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item
    else:
        # Create new cart item
        cart_item = CartItem(
            cart_id=cart.id,
            food_item_id=item_data.food_item_id,
            quantity=item_data.quantity
        )
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
        return cart_item


@router.put("/items/{item_id}", response_model=CartItemSchema)
def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    cart = get_or_create_cart(db, current_user.id)
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    cart_item.quantity = item_data.quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item


@router.delete("/items/{item_id}")
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    cart = get_or_create_cart(db, current_user.id)
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    item_name = cart_item.food_item.name
    db.delete(cart_item)
    db.commit()
    
    return {"message": f"'{item_name}' removed from cart"}


@router.delete("/clear")
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all items from cart"""
    cart = get_or_create_cart(db, current_user.id)
    
    # Delete all cart items
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    
    return {"message": "Cart cleared successfully"}


@router.post("/items/{item_id}/increase")
def increase_item_quantity(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Increase cart item quantity by 1"""
    cart = get_or_create_cart(db, current_user.id)
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    cart_item.quantity += 1
    db.commit()
    db.refresh(cart_item)
    
    return {"message": f"Quantity increased for '{cart_item.food_item.name}'", "item": cart_item}


@router.post("/items/{item_id}/decrease")
def decrease_item_quantity(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Decrease cart item quantity by 1, remove if quantity becomes 0"""
    cart = get_or_create_cart(db, current_user.id)
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    cart_item.quantity -= 1
    
    if cart_item.quantity <= 0:
        item_name = cart_item.food_item.name
        db.delete(cart_item)
        db.commit()
        return {"message": f"'{item_name}' removed from cart"}
    else:
        db.commit()
        db.refresh(cart_item)
        return {"message": f"Quantity decreased for '{cart_item.food_item.name}'", "item": cart_item}
