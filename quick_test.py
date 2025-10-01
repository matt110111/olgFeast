#!/usr/bin/env python3
"""
Quick Site Functionality Test
Simple script to test key functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Transaction

def test_basic_functionality():
    """Test basic site functionality"""
    print("🧪 Testing olgFeast Site Functionality")
    print("=" * 40)
    
    client = Client()
    results = []
    
    # Test 1: User Registration/Login
    try:
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Check Profile was created
        profile = Profile.objects.get(user=user)
        results.append(("User & Profile Creation", True, "✅ User and Profile created"))
        
    except Exception as e:
        results.append(("User & Profile Creation", False, f"❌ {str(e)}"))
    
    # Test 2: Login
    try:
        response = client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        success = response.status_code in [200, 302]
        results.append(("User Login", success, f"Status: {response.status_code}"))
    except Exception as e:
        results.append(("User Login", False, f"❌ {str(e)}"))
    
    # Test 3: Shop Pages
    try:
        client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        response = client.get('/shop/')
        success = response.status_code == 200
        results.append(("Shop Home Page", success, f"Status: {response.status_code}"))
    except Exception as e:
        results.append(("Shop Home Page", False, f"❌ {str(e)}"))
    
    # Test 4: Food Items
    try:
        food_count = FoodItem.objects.count()
        results.append(("Food Items Available", food_count > 0, f"Found {food_count} items"))
    except Exception as e:
        results.append(("Food Items", False, f"❌ {str(e)}"))
    
    # Test 5: Add to Cart
    try:
        client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        if FoodItem.objects.exists():
            food_item = FoodItem.objects.first()
            response = client.get(f'/cart/add-to-cart/{food_item.id}/')
            success = response.status_code in [200, 302]
            results.append(("Add to Cart", success, f"Status: {response.status_code}"))
        else:
            results.append(("Add to Cart", False, "No food items available"))
    except Exception as e:
        results.append(("Add to Cart", False, f"❌ {str(e)}"))
    
    # Test 6: Order Tracking
    try:
        client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        response = client.get('/cart/order-tracking/')
        success = response.status_code == 200
        results.append(("Order Tracking Page", success, f"Status: {response.status_code}"))
    except Exception as e:
        results.append(("Order Tracking Page", False, f"❌ {str(e)}"))
    
    # Test 7: Transactions
    try:
        transaction_count = Transaction.objects.count()
        results.append(("Transaction System", True, f"Found {transaction_count} transactions"))
    except Exception as e:
        results.append(("Transaction System", False, f"❌ {str(e)}"))
    
    # Test 8: Status Field
    try:
        if Transaction.objects.exists():
            transaction = Transaction.objects.first()
            has_status = hasattr(transaction, 'status')
            results.append(("Order Status Field", has_status, f"Status field exists: {has_status}"))
        else:
            results.append(("Order Status Field", True, "No transactions to test"))
    except Exception as e:
        results.append(("Order Status Field", False, f"❌ {str(e)}"))
    
    # Print Results
    print("\n📋 Test Results:")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success, message in results:
        print(f"{'✅' if success else '❌'} {test_name}: {message}")
        if success:
            passed += 1
    
    print("\n📊 Summary:")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Site is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the results above.")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
