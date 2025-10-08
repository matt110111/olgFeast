#!/usr/bin/env python3
"""
Database setup script for olgFeast FastAPI application
Creates tables and seeds initial data
"""
import asyncio
from app.core.database import engine
from app.models import user, menu, cart, order
from app.core.config import settings
from app.services.menu_service import MenuService
from app.services.cart_service import CartService
from app.services.order_service import OrderService
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    
    # Import all models to ensure they're registered
    from app.models.user import User, Profile
    from app.models.menu import FoodItem
    from app.models.cart import Cart, CartItem
    from app.models.order import Order, OrderItem
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(user.Base.metadata.create_all)
        await conn.run_sync(menu.Base.metadata.create_all)
        await conn.run_sync(cart.Base.metadata.create_all)
        await conn.run_sync(order.Base.metadata.create_all)
    
    logger.info("✅ Database tables created successfully")

async def seed_initial_data():
    """Seed the database with initial data"""
    logger.info("Seeding initial data...")
    
    from app.core.database import AsyncSessionLocal
    from app.models.user import User, Profile
    from app.models.menu import FoodItem
    from app.models.cart import Cart
    from app.models.order import Order, OrderItem
    
    # Generate secure passwords
    import secrets
    import string
    
    def generate_password(length=12):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    admin_password = generate_password()
    customer_password = generate_password()
    
    async with AsyncSessionLocal() as session:
        try:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@olgfeast.com",
                hashed_password=get_password_hash(admin_password),
                is_active=True,
                is_staff=True
            )
            session.add(admin_user)
            await session.flush()
            
            admin_profile = Profile(
                user_id=admin_user.id,
                phone_number="+1234567890",
                address="123 Admin St, Admin City, AC 12345"
            )
            session.add(admin_profile)
            
            # Create customer user
            customer_user = User(
                username="customer",
                email="customer@olgfeast.com",
                hashed_password=get_password_hash(customer_password),
                is_active=True,
                is_staff=False
            )
            session.add(customer_user)
            await session.flush()
            
            customer_profile = Profile(
                user_id=customer_user.id,
                phone_number="+0987654321",
                address="456 Customer Ave, Customer Town, CT 54321"
            )
            session.add(customer_profile)
            
            # Create food items
            food_items = [
                FoodItem(
                    food_group="Main Course",
                    name="Grilled Chicken Breast",
                    value=15.99,
                    ticket=3,
                    description="Tender grilled chicken breast with herbs",
                    is_available=True
                ),
                FoodItem(
                    food_group="Main Course",
                    name="Beef Burger",
                    value=12.99,
                    ticket=2,
                    description="Juicy beef burger with fresh vegetables",
                    is_available=True
                ),
                FoodItem(
                    food_group="Appetizer",
                    name="Caesar Salad",
                    value=8.99,
                    ticket=1,
                    description="Fresh romaine lettuce with caesar dressing",
                    is_available=True
                ),
                FoodItem(
                    food_group="Appetizer",
                    name="Buffalo Wings",
                    value=10.99,
                    ticket=2,
                    description="Spicy buffalo wings with ranch dip",
                    is_available=True
                ),
                FoodItem(
                    food_group="Dessert",
                    name="Chocolate Cake",
                    value=6.99,
                    ticket=1,
                    description="Rich chocolate cake with vanilla ice cream",
                    is_available=True
                ),
                FoodItem(
                    food_group="Beverage",
                    name="Fresh Orange Juice",
                    value=3.99,
                    ticket=1,
                    description="Freshly squeezed orange juice",
                    is_available=True
                ),
                FoodItem(
                    food_group="Beverage",
                    name="Coffee",
                    value=2.99,
                    ticket=1,
                    description="Premium roasted coffee",
                    is_available=True
                ),
                FoodItem(
                    food_group="Main Course",
                    name="Fish and Chips",
                    value=14.99,
                    ticket=2,
                    description="Beer-battered fish with crispy fries",
                    is_available=True
                ),
                FoodItem(
                    food_group="Main Course",
                    name="Vegetarian Pasta",
                    value=11.99,
                    ticket=2,
                    description="Penne pasta with seasonal vegetables",
                    is_available=True
                ),
                FoodItem(
                    food_group="Dessert",
                    name="Ice Cream Sundae",
                    value=5.99,
                    ticket=1,
                    description="Vanilla ice cream with chocolate sauce",
                    is_available=True
                )
            ]
            
            for item in food_items:
                session.add(item)
            
            await session.commit()
            logger.info("✅ Initial data seeded successfully")
            
            return admin_password, customer_password
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error seeding data: {e}")
            raise

async def generate_credentials_file(admin_password, customer_password):
    """Generate credentials file for deployment"""
    import os
    from datetime import datetime
    
    credentials_content = f"""OlgFeast Deployment Credentials
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Admin User:
  Username: admin
  Password: {admin_password}
  Role: Staff/Admin

Customer User:
  Username: customer
  Password: {customer_password}
  Role: Customer

⚠️  IMPORTANT SECURITY NOTES:
1. Change these passwords immediately after first login
2. These credentials are for initial setup only
3. Delete this file after noting the credentials
4. Use strong, unique passwords in production

Access URLs:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
"""
    
    # Ensure logs directory exists
    logs_dir = "/app/logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Write credentials file
    credentials_file = os.path.join(logs_dir, "deployment_credentials.txt")
    try:
        with open(credentials_file, "w") as f:
            f.write(credentials_content)
        logger.info(f"✅ Credentials saved to: {credentials_file}")
        logger.info("👤 Generated credentials:")
        logger.info(f"   Admin: admin / {admin_password}")
        logger.info(f"   Customer: customer / {customer_password}")
    except Exception as e:
        logger.error(f"❌ Could not save credentials file: {e}")
        logger.info("👤 Demo credentials (not saved to file):")
        logger.info("   Admin: admin / admin123")
        logger.info("   Customer: customer / customer123")

async def main():
    """Main setup function"""
    try:
        await create_tables()
        admin_password, customer_password = await seed_initial_data()
        await generate_credentials_file(admin_password, customer_password)
        logger.info("🎉 Database setup completed successfully!")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
