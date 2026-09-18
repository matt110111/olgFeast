from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FoodItemBase(BaseModel):
    food_group: str
    name: str
    value: float = Field(default=0, ge=0, le=1000000)
    ticket: int = Field(default=1, ge=0, le=10000)
    description: Optional[str] = None
    is_available: bool = True


class FoodItemCreate(FoodItemBase):
    pass


class FoodItemUpdate(BaseModel):
    food_group: Optional[str] = None
    name: Optional[str] = None
    value: Optional[float] = Field(default=None, ge=0, le=1000000)
    ticket: Optional[int] = Field(default=None, ge=0, le=10000)
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
