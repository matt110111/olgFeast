#!/usr/bin/env python3
"""
Database Setup Script for OlgFeast Production Deployment
This script creates a clean database with proper initialization for production use.
"""

import os
import sys
import asyncio
import hashlib
import secrets
from pathlib import Path

# Add the fastapi_app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "fastapi_app"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.menu import FoodItem
from app.core.security import get_password_hash

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(32)

def generate_admin_password():
    """Generate a secure random admin password"""
    return secrets.token_urlsafe(16)

def generate_customer_password():
    """Generate a secure random customer password"""
    return secrets.token_urlsafe(12)

def setup_database():
    """Initialize the database with tables and basic data"""
    print("🗄️  Setting up OlgFeast database...")
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create tables
    print("📋 Creating database tables...")
    from app.models import user, menu, cart, order
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Check if users already exist
        existing_users = session.query(User).count()
        if existing_users > 0:
            print("⚠️  Users already exist in database. Skipping user creation.")
            return
        
        # Generate secure passwords
        admin_password = generate_admin_password()
        customer_password = generate_customer_password()
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@olgfeast.com",
            hashed_password=get_password_hash(admin_password),
            is_staff=True,
            is_active=True
        )
        session.add(admin_user)
        
        # Create customer user
        customer_user = User(
            username="customer",
            email="customer@olgfeast.com",
            hashed_password=get_password_hash(customer_password),
            is_staff=False,
            is_active=True
        )
        session.add(customer_user)
        
        # Create sample food items
        print("🍽️  Creating menu items...")
        
        # Add sample food items
        food_items = [
            # Appetizers
            {"food_group": "Appetizers", "name": "Caesar Salad", "description": "Fresh romaine lettuce, croutons, parmesan cheese", "value": 8.99, "ticket": 10},
            {"food_group": "Appetizers", "name": "Garlic Bread", "description": "Crusty bread with garlic butter", "value": 4.99, "ticket": 5},
            {"food_group": "Appetizers", "name": "Wings", "description": "Buffalo wings with blue cheese dip", "value": 12.99, "ticket": 15},
            
            # Main Courses
            {"food_group": "Main Courses", "name": "Grilled Salmon", "description": "Fresh Atlantic salmon with lemon herb butter", "value": 18.99, "ticket": 20},
            {"food_group": "Main Courses", "name": "Beef Steak", "description": "8oz ribeye steak cooked to perfection", "value": 24.99, "ticket": 25},
            {"food_group": "Main Courses", "name": "Chicken Alfredo", "description": "Creamy fettuccine alfredo with grilled chicken", "value": 16.99, "ticket": 18},
            {"food_group": "Main Courses", "name": "Vegetarian Pasta", "description": "Penne pasta with seasonal vegetables", "value": 14.99, "ticket": 15},
            
            # Desserts
            {"food_group": "Desserts", "name": "Chocolate Cake", "description": "Rich chocolate cake with ganache", "value": 6.99, "ticket": 5},
            {"food_group": "Desserts", "name": "Tiramisu", "description": "Classic Italian dessert", "value": 7.99, "ticket": 5},
            {"food_group": "Desserts", "name": "Ice Cream", "description": "Vanilla, chocolate, or strawberry", "value": 4.99, "ticket": 2},
            
            # Beverages
            {"food_group": "Beverages", "name": "Coffee", "description": "Freshly brewed coffee", "value": 2.99, "ticket": 3},
            {"food_group": "Beverages", "name": "Fresh Juice", "description": "Orange, apple, or cranberry juice", "value": 3.99, "ticket": 2},
            {"food_group": "Beverages", "name": "Soft Drinks", "description": "Coke, Pepsi, Sprite, or Diet options", "value": 2.49, "ticket": 1},
        ]
        
        for item_data in food_items:
            food_item = FoodItem(**item_data)
            session.add(food_item)
        
        # Commit all changes
        session.commit()
        
        print("✅ Database setup completed successfully!")
        print("\n📋 Generated Credentials:")
        print(f"   Admin User: admin / {admin_password}")
        print(f"   Customer User: customer / {customer_password}")
        print("\n⚠️  IMPORTANT: Save these credentials securely!")
        print("   You can change them later through the admin panel.")
        
        # Save credentials to file
        credentials_file = Path("deployment_credentials.txt")
        with open(credentials_file, "w") as f:
            f.write("OlgFeast Deployment Credentials\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Admin User: admin / {admin_password}\n")
            f.write(f"Customer User: customer / {customer_password}\n\n")
            f.write("⚠️ IMPORTANT: Change these passwords after first login!\n")
            f.write("⚠️ Keep this file secure and delete after use!\n")
        
        print(f"\n💾 Credentials saved to: {credentials_file}")
        print("   Please delete this file after noting the credentials!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def cleanup_database():
    """Clean up the database (drop all tables)"""
    print("🧹 Cleaning up database...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    # Drop all tables
    from app.models import user, menu, cart, order
    from app.core.database import Base
    Base.metadata.drop_all(bind=engine)
    
    print("✅ Database cleanup completed!")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_database()
    else:
        setup_database()

if __name__ == "__main__":
    main()
