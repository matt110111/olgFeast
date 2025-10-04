from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FoodItemBase(BaseModel):
    food_group: str
    name: str
    value: float = 0.0
    ticket: int = 1
    description: Optional[str] = None
    is_available: bool = True


class FoodItemCreate(FoodItemBase):
    pass


class FoodItemUpdate(BaseModel):
    food_group: Optional[str] = None
    name: Optional[str] = None
    value: Optional[float] = None
    ticket: Optional[int] = None
    description: Optional[str] = None
    is_available: Optional[bool] = None


class FoodItem(FoodItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FoodItemGroup(BaseModel):
    group: str
    items: list[FoodItem]
