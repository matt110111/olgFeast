#!/usr/bin/env python
"""
Detailed test for add to cart functionality
"""

import os
import sys
import django

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Item, Inventory

def test_add_to_cart():
    """Test the add to cart functionality in detail"""
    print("🧪 Testing Add to Cart Functionality")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Create test user (or get existing)
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    profile, profile_created = Profile.objects.get_or_create(user=user)
    
    # Create test food item
    food_item = FoodItem.objects.create(
        name="Test Item",
        food_group="Test Group",
        value=10.99,
        ticket=5
    )
    
    print(f"✅ Created test user: {user.username}")
    print(f"✅ Created test food item: {food_item.name} (ID: {food_item.id})")
    
    # Login user
    login_success = client.login(username='testuser', password='testpass123')
    print(f"✅ User login: {'Success' if login_success else 'Failed'}")
    
    # Test adding item to cart
    try:
        response = client.get(f'/cart/add-to-cart/{food_item.id}/')
        print(f"✅ Add to cart response: {response.status_code}")
        
        # Check if item was added to cart
        profile = Profile.objects.get(user=user)
        cart_items = profile.inventory.item_set.all()
        
        print(f"✅ Cart items count: {cart_items.count()}")
        
        if cart_items.exists():
            cart_item = cart_items.first()
            print(f"✅ Cart item: {cart_item.name}")
            print(f"✅ Cart item quantity: {cart_item.quantity}")
            print(f"✅ Cart item value: {cart_item.value}")
            print(f"✅ Cart item tickets: {cart_item.ticket}")
            
            # Test adding same item again (should increase quantity)
            response2 = client.get(f'/cart/add-to-cart/{food_item.id}/')
            cart_item.refresh_from_db()
            print(f"✅ After second add - quantity: {cart_item.quantity}")
            
            # Test order summary page
            response3 = client.get('/cart/order-summary/')
            print(f"✅ Order summary response: {response3.status_code}")
            
        else:
            print("❌ No items found in cart")
            
    except Exception as e:
        print(f"❌ Error testing add to cart: {e}")
    
    # Test with invalid item ID
    try:
        response = client.get('/cart/add-to-cart/99999/')
        print(f"✅ Invalid item ID response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error with invalid item: {e}")
    
    # Cleanup
    food_item.delete()
    print("✅ Cleanup completed (keeping test user for future tests)")
    
    print("\n🎉 Add to cart test completed!")

if __name__ == '__main__':
    test_add_to_cart()
