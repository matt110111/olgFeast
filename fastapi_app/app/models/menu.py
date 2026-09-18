from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from ..core.database import Base


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    food_group = Column(String(40), nullable=False, index=True)
    name = Column(String(40), nullable=False)
    value = Column(Float, default=0.0)
    ticket = Column(Integer, default=1)
    description = Column(String(500))
    is_available = Column(String(10), default="true")  # Using string for SQLite compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<FoodItem(id={self.id}, name='{self.name}', group='{self.food_group}')>"
