from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...models.menu import FoodItem
from ...schemas.menu import FoodItem as FoodItemSchema, FoodItemCreate, FoodItemUpdate, FoodItemGroup
from ...api.deps import get_current_user, get_current_staff_user
from ...models.user import User

router = APIRouter()


@router.get("/items", response_model=List[FoodItemSchema])
def get_food_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    food_group: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all food items with optional filtering"""
    query = db.query(FoodItem)
    
    if food_group:
        query = query.filter(FoodItem.food_group == food_group)
    
    items = query.offset(skip).limit(limit).all()
    return items


@router.get("/items/groups", response_model=List[FoodItemGroup])
def get_food_groups(db: Session = Depends(get_db)):
    """Get all food items grouped by category"""
    from sqlalchemy import func
    
    # Get all distinct food groups
    groups = db.query(FoodItem.food_group).distinct().all()
    
    result = []
    for (group_name,) in groups:
        items = db.query(FoodItem).filter(FoodItem.food_group == group_name).all()
        result.append(FoodItemGroup(group=group_name, items=items))
    
    return result


@router.get("/items/{item_id}", response_model=FoodItemSchema)
def get_food_item(item_id: int, db: Session = Depends(get_db)):
    """Get a specific food item by ID"""
    item = db.query(FoodItem).filter(FoodItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found"
        )
    return item


@router.post("/items", response_model=FoodItemSchema)
def create_food_item(
    item_data: FoodItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new food item (staff only)"""
    db_item = FoodItem(**item_data.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/items/{item_id}", response_model=FoodItemSchema)
def update_food_item(
    item_id: int,
    item_data: FoodItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a food item (staff only)"""
    db_item = db.query(FoodItem).filter(FoodItem.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found"
        )
    
    # Update only provided fields
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/items/{item_id}")
def delete_food_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Delete a food item (staff only)"""
    db_item = db.query(FoodItem).filter(FoodItem.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found"
        )
    
    item_name = db_item.name
    db.delete(db_item)
    db.commit()
    
    return {"message": f"Food item '{item_name}' deleted successfully"}
