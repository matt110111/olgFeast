from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .menu import FoodItem


class CartItemBase(BaseModel):
    food_item_id: int
    quantity: int = Field(default=1, ge=1, le=999)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=999)


class CartItem(CartItemBase):
    id: int
    cart_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    food_item: FoodItem

    class Config:
        from_attributes = True


class CartBase(BaseModel):
    pass


class Cart(CartBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: list[CartItem] = []

    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    total_items: int
    total_value: float
    total_tickets: int
    items: list[CartItem]
