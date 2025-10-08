#!/usr/bin/env python3
"""
Script to seed the database with initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.menu import FoodItem
from app.models.user import User
from app.models.cart import Cart
from app.models.order import Order
from app.core.security import get_password_hash

def seed_database():
    """Seed the database with initial data"""
    db = SessionLocal()
    
    try:
        # Check if we already have data
        if db.query(FoodItem).count() > 0:
            print("Database already has data. Skipping seed.")
            return
        
        # Create sample food items
        food_items = [
            FoodItem(
                food_group="Appetizers",
                name="Buffalo Wings",
                value=12.99,
                ticket=1
            ),
            FoodItem(
                food_group="Appetizers", 
                name="Mozzarella Sticks",
                value=8.99,
                ticket=1
            ),
            FoodItem(
                food_group="Main Course",
                name="Grilled Salmon",
                value=24.99,
                ticket=2
            ),
            FoodItem(
                food_group="Main Course",
                name="Chicken Parmesan",
                value=18.99,
                ticket=2
            ),
            FoodItem(
                food_group="Main Course",
                name="Ribeye Steak",
                value=32.99,
                ticket=3
            ),
            FoodItem(
                food_group="Desserts",
                name="Chocolate Cake",
                value=7.99,
                ticket=1
            ),
            FoodItem(
                food_group="Desserts",
                name="Tiramisu",
                value=8.99,
                ticket=1
            ),
            FoodItem(
                food_group="Beverages",
                name="Fresh Orange Juice",
                value=4.99,
                ticket=1
            ),
            FoodItem(
                food_group="Beverages",
                name="Craft Beer",
                value=6.99,
                ticket=1
            ),
            FoodItem(
                food_group="Salads",
                name="Caesar Salad",
                value=11.99,
                ticket=1
            ),
            FoodItem(
                food_group="Salads",
                name="Greek Salad",
                value=12.99,
                ticket=1
            ),
        ]
        
        # Add food items to database
        for item in food_items:
            db.add(item)
        
        # Create a test staff user
        staff_user = User(
            username="admin",
            email="admin@olgfeast.com",
            hashed_password=get_password_hash("admin123"),
            is_staff=True,
            is_active=True
        )
        db.add(staff_user)
        
        # Create a test customer user
        customer_user = User(
            username="customer",
            email="customer@example.com",
            hashed_password=get_password_hash("customer123"),
            is_staff=False,
            is_active=True
        )
        db.add(customer_user)
        
        # Commit all changes
        db.commit()
        
        print("✅ Database seeded successfully!")
        print(f"   - {len(food_items)} food items created")
        print("   - 2 test users created (admin/customer)")
        print("\n📋 Test Credentials:")
        print("   Staff User: admin / admin123")
        print("   Customer User: customer / customer123")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
