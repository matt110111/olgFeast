from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.menu import FoodItem
from ..schemas.menu import FoodItemCreate, FoodItemUpdate


class MenuService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_food_items(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        food_group: Optional[str] = None
    ) -> List[FoodItem]:
        """Get food items with optional filtering"""
        query = self.db.query(FoodItem)
        
        if food_group:
            query = query.filter(FoodItem.food_group == food_group)
        
        return query.offset(skip).limit(limit).all()
    
    def get_food_item(self, item_id: int) -> Optional[FoodItem]:
        """Get a specific food item by ID"""
        return self.db.query(FoodItem).filter(FoodItem.id == item_id).first()
    
    def create_food_item(self, item_data: FoodItemCreate) -> FoodItem:
        """Create a new food item"""
        db_item = FoodItem(**item_data.model_dump())
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def update_food_item(self, item_id: int, item_data: FoodItemUpdate) -> Optional[FoodItem]:
        """Update a food item"""
        db_item = self.db.query(FoodItem).filter(FoodItem.id == item_id).first()
        if not db_item:
            return None
        
        # Update only provided fields
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        self.db.commit()
        self.db.refresh(db_item)
        return db_item
    
    def delete_food_item(self, item_id: int) -> bool:
        """Delete a food item"""
        db_item = self.db.query(FoodItem).filter(FoodItem.id == item_id).first()
        if not db_item:
            return False
        
        self.db.delete(db_item)
        self.db.commit()
        return True
    
    def get_food_groups(self) -> List[str]:
        """Get all distinct food groups"""
        groups = self.db.query(FoodItem.food_group).distinct().all()
        return [group[0] for group in groups]
