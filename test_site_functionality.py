#!/usr/bin/env python3
"""
Comprehensive Site Functionality Test Script
Tests all major features of the olgFeast Django application
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
django.setup()

from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Inventory, Item, Transaction

class SiteFunctionalityTest:
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.test_profile = None
        self.test_items = []
        self.test_transactions = []
        self.results = []
        
    def log_result(self, test_name, status, message=""):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        result = f"{status_symbol} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.results.append((test_name, status, message))
    
    def setup_test_data(self):
        """Create test data for testing"""
        try:
            # Create test user
            self.test_user, created = User.objects.get_or_create(
                username='test_user',
                defaults={
                    'email': 'test@example.com',
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                self.test_user.set_password('testpass123')
                self.test_user.save()
                
            # Get or create profile
            self.test_profile, created = Profile.objects.get_or_create(
                user=self.test_user
            )
            
            # Create test food items
            test_foods = [
                {'food_group': 'Main', 'name': 'Test Burger', 'value': 12.99, 'ticket': 1},
                {'food_group': 'Side', 'name': 'Test Fries', 'value': 5.99, 'ticket': 1},
                {'food_group': 'Drink', 'name': 'Test Soda', 'value': 2.99, 'ticket': 1},
            ]
            
            for food_data in test_foods:
                food, created = FoodItem.objects.get_or_create(
                    name=food_data['name'],
                    defaults=food_data
                )
                self.test_items.append(food)
                
            self.log_result("Setup Test Data", True, f"Created {len(self.test_items)} test items")
            return True
            
        except Exception as e:
            self.log_result("Setup Test Data", False, str(e))
            return False
    
    def test_user_authentication(self):
        """Test user login/logout functionality"""
        try:
            # Test login
            response = self.client.post('/login/', {
                'username': 'test_user',
                'password': 'testpass123'
            })
            success = response.status_code in [200, 302]
            self.log_result("User Login", success, f"Status: {response.status_code}")
            
            # Test logout
            response = self.client.get('/logout/')
            success = response.status_code in [200, 302]
            self.log_result("User Logout", success, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("User Authentication", False, str(e))
            return False
    
    def test_shop_front_pages(self):
        """Test shop front pages load correctly"""
        try:
            # Login first
            self.client.post('/login/', {
                'username': 'test_user',
                'password': 'testpass123'
            })
            
            # Test home page
            response = self.client.get('/shop/')
            success = response.status_code == 200
            self.log_result("Shop Home Page", success, f"Status: {response.status_code}")
            
            # Test detail page
            if self.test_items:
                response = self.client.get(f'/shop/item/{self.test_items[0].id}/')
                success = response.status_code == 200
                self.log_result("Item Detail Page", success, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Shop Front Pages", False, str(e))
            return False
    
    def test_add_to_cart(self):
        """Test adding items to cart"""
        try:
            # Login first
            self.client.post('/login/', {
                'username': 'test_user',
                'password': 'testpass123'
            })
            
            if not self.test_items:
                self.log_result("Add to Cart", False, "No test items available")
                return False
                
            # Add item to cart
            response = self.client.get(f'/cart/add-to-cart/{self.test_items[0].id}/')
            success = response.status_code in [200, 302]
            self.log_result("Add to Cart", success, f"Status: {response.status_code}")
            
            # Check cart contents
            response = self.client.get('/cart/order-summary/')
            success = response.status_code == 200
            self.log_result("View Cart", success, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Add to Cart", False, str(e))
            return False
    
    def test_cart_manipulation(self):
        """Test cart quantity manipulation"""
        try:
            # Login first
            self.client.post('/login/', {
                'username': 'test_user',
                'password': 'testpass123'
            })
            
            # Get user's inventory items
            profile = Profile.objects.get(user=self.test_user)
            inventory = profile.inventory
            items = inventory.item_set.all()
            
            if not items:
                self.log_result("Cart Manipulation", False, "No items in cart")
                return False
                
            # Test quantity increase
            first_item = items.first()
            response = self.client.get(f'/cart/item/quantity/{first_item.id}/up/')
            success = response.status_code in [200, 302]
            self.log_result("Increase Quantity", success, f"Status: {response.status_code}")
            
            # Test quantity decrease
            response = self.client.get(f'/cart/item/quantity/{first_item.id}/down/')
            success = response.status_code in [200, 302]
            self.log_result("Decrease Quantity", success, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Cart Manipulation", False, str(e))
            return False
    
    def test_checkout_process(self):
        """Test complete checkout process"""
        try:
            # Login first
            self.client.post('/login/', {
                'username': 'test_user',
                'password': 'testpass123'
            })
            
            # Go to checkout
            response = self.client.get('/cart/checkout/')
            success = response.status_code in [200, 302]
            self.log_result("Checkout Page", success, f"Status: {response.status_code}")
            
            # Complete transaction
            response = self.client.get('/cart/transacyion/')
            success = response.status_code in [200, 302]
            self.log_result("Complete Transaction", success, f"Status: {response.status_code}")
            
            # Check success page
            response = self.client.get('/cart/success/')
            success = response.status_code in [200, 302]
            self.log_result("Success Page", success, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Checkout Process", False, str(e))
            return False
    
    def test_order_tracking(self):
        """Test order tracking functionality"""
        try:
            # Login first
            self.client.post('/login/', {
                'username': 'test_user',
                'password': 'testpass123'
            })
            
            # Test order tracking page
            response = self.client.get('/cart/order-tracking/')
            success = response.status_code == 200
            self.log_result("Order Tracking Page", success, f"Status: {response.status_code}")
            
            # Check if orders exist
            orders = Transaction.objects.all()
            self.log_result("Orders in Database", True, f"Found {orders.count()} orders")
            
            # Test status update (if orders exist and user is staff)
            if orders.exists() and self.test_user.is_staff:
                first_order = orders.first()
                if first_order.status != 'complete':
                    next_status = 'preparing' if first_order.status == 'pending' else 'ready'
                    response = self.client.get(f'/cart/update-status/{first_order.id}/{next_status}/')
                    success = response.status_code in [200, 302]
                    self.log_result("Status Update", success, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Order Tracking", False, str(e))
            return False
    
    def test_model_functionality(self):
        """Test model methods and relationships"""
        try:
            # Test Profile-Inventory relationship
            profile = Profile.objects.get(user=self.test_user)
            inventory = profile.inventory
            self.log_result("Profile-Inventory Relationship", inventory is not None)
            
            # Test Transaction methods
            transactions = Transaction.objects.all()
            if transactions.exists():
                order = transactions.first()
                
                # Test total calculation methods
                total_tickets = order.get_total_tickets()
                total_value = order.get_total_value()
                item_summary = order.get_item_summary()
                
                self.log_result("Transaction Total Tickets", total_tickets >= 0, f"Value: {total_tickets}")
                self.log_result("Transaction Total Value", total_value >= 0, f"Value: {total_value}")
                self.log_result("Transaction Item Summary", isinstance(item_summary, dict), f"Items: {len(item_summary)}")
                
                # Test status field
                self.log_result("Transaction Status Field", order.status in ['pending', 'preparing', 'ready', 'complete'], f"Status: {order.status}")
            
            return True
            
        except Exception as e:
            self.log_result("Model Functionality", False, str(e))
            return False
    
    def test_url_patterns(self):
        """Test that all URL patterns are accessible"""
        try:
            # Login first
            self.client.post('/login/', {
                'username': 'test_user',
                'password': 'testpass123'
            })
            
            # Test key URL patterns
            urls_to_test = [
                ('/shop/', 'Shop Home'),
                ('/cart/order-summary/', 'Cart Summary'),
                ('/cart/order-tracking/', 'Order Tracking'),
                ('/cart/checkout/', 'Checkout'),
                ('/cart/transacyion/', 'Transaction'),
            ]
            
            for url, name in urls_to_test:
                response = self.client.get(url)
                success = response.status_code in [200, 302]
                self.log_result(f"URL: {name}", success, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("URL Patterns", False, str(e))
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Clean up transactions
            Transaction.objects.filter(owner=self.test_profile).delete()
            
            # Clean up cart items
            if self.test_profile.inventory:
                self.test_profile.inventory.item_set.all().delete()
            
            self.log_result("Cleanup Test Data", True)
            return True
            
        except Exception as e:
            self.log_result("Cleanup Test Data", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests and return summary"""
        print("🧪 Starting olgFeast Site Functionality Tests")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        print("\n📋 Running Tests...")
        print("-" * 30)
        
        # Run all tests
        tests = [
            self.test_user_authentication,
            self.test_shop_front_pages,
            self.test_add_to_cart,
            self.test_cart_manipulation,
            self.test_checkout_process,
            self.test_order_tracking,
            self.test_model_functionality,
            self.test_url_patterns,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {str(e)}")
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 50)
        passed = sum(1 for _, status, _ in self.results if status)
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! Site functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the results above.")
            print("\nFailed Tests:")
            for name, status, message in self.results:
                if not status:
                    print(f"  ❌ {name}: {message}")
        
        return passed == total

def main():
    """Main function to run tests"""
    try:
        tester = SiteFunctionalityTest()
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test runner failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
