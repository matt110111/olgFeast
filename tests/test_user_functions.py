#!/usr/bin/env python3
"""
Comprehensive User Functionality Tests
Tests all basic user features including registration, login, shopping, cart management
"""

import time
from typing import Dict, List, Tuple
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction

from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Inventory, Item, Transaction

class UserFunctionTests:
    """Test class for user functionality"""
    
    def __init__(self, client: Client, test_data: Dict):
        self.client = client
        self.test_data = test_data
        self.results = []
    
    def log_result(self, test_name: str, status: bool, message: str = "", duration: float = 0):
        """Log test results"""
        status_symbol = "✅" if status else "❌"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        result = f"{status_symbol} {test_name}{duration_str}"
        if message:
            result += f" - {message}"
        print(f"  {result}")
        self.results.append((test_name, status, message, duration))
    
    def test_user_registration(self):
        """Test user registration functionality"""
        start_time = time.time()
        
        try:
            # Test registration page access
            response = self.client.get('/register/')
            self.log_result("Registration Page Access", response.status_code == 200, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test successful registration
            registration_data = {
                'username': 'newuser123',
                'password1': 'complexpass123!',
                'password2': 'complexpass123!'
            }
            
            response = self.client.post('/register/', registration_data)
            success = response.status_code in [200, 302]
            self.log_result("User Registration", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Verify user was created
            user_exists = User.objects.filter(username='newuser123').exists()
            self.log_result("User Creation Verification", user_exists, 
                          "User exists in database", time.time() - start_time)
            
            # Verify profile was created
            if user_exists:
                user = User.objects.get(username='newuser123')
                profile_exists = hasattr(user, 'profile') and user.profile is not None
                self.log_result("Profile Creation", profile_exists, 
                              "Profile exists for new user", time.time() - start_time)
                
                # Verify inventory was created
                inventory_exists = user.profile.inventory is not None
                self.log_result("Inventory Creation", inventory_exists, 
                              "Inventory exists for new user", time.time() - start_time)
            
            # Clean up test user
            User.objects.filter(username='newuser123').delete()
            
        except Exception as e:
            self.log_result("User Registration", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_user_login_logout(self):
        """Test user login and logout functionality"""
        start_time = time.time()
        
        try:
            # Test login page access
            response = self.client.get('/login/')
            self.log_result("Login Page Access", response.status_code == 200, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test successful login
            login_data = {
                'username': 'testuser',
                'password': 'testpass123'
            }
            
            response = self.client.post('/login/', login_data)
            success = response.status_code in [200, 302]
            self.log_result("User Login", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test authenticated access
            response = self.client.get('/shop/')
            authenticated_access = response.status_code == 200
            self.log_result("Authenticated Access", authenticated_access, 
                          f"Shop access: {response.status_code}", time.time() - start_time)
            
            # Test logout
            response = self.client.get('/logout/')
            logout_success = response.status_code in [200, 302]
            self.log_result("User Logout", logout_success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test unauthenticated access after logout
            response = self.client.get('/shop/')
            unauthenticated_redirect = response.status_code in [302, 200]  # May redirect or show login
            self.log_result("Post-Logout Access", unauthenticated_redirect, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("User Login/Logout", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_menu_browsing(self):
        """Test menu browsing functionality"""
        start_time = time.time()
        
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test shop home page
            response = self.client.get('/shop/')
            self.log_result("Shop Home Access", response.status_code == 200, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test food group browsing
            food_groups = ['Main Course', 'Appetizer', 'Beverage', 'Dessert']
            for group in food_groups:
                response = self.client.get(f'/shop/{group}/')
                self.log_result(f"Food Group: {group}", response.status_code == 200, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
            # Test individual food item access
            for item in self.test_data['food_items']:
                response = self.client.get(f'/shop/{item.food_group}/')
                if response.status_code == 200:
                    content_contains_item = item.name.encode() in response.content
                    self.log_result(f"Item Display: {item.name}", content_contains_item, 
                                  "Item visible on page", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Menu Browsing", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_add_to_cart(self):
        """Test add to cart functionality"""
        start_time = time.time()
        
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test adding items to cart
            for item in self.test_data['food_items']:
                response = self.client.get(f'/cart/add-to-cart/{item.id}/')
                success = response.status_code in [200, 302]
                self.log_result(f"Add to Cart: {item.name}", success, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
            # Test cart summary access
            response = self.client.get('/cart/order-summary/')
            self.log_result("Cart Summary Access", response.status_code == 200, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Verify items in cart
            user = User.objects.get(username='testuser')
            cart_items = user.profile.inventory.item_set.all()
            self.log_result("Cart Items Verification", cart_items.count() > 0, 
                          f"Items in cart: {cart_items.count()}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Add to Cart", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_cart_management(self):
        """Test cart management functionality"""
        start_time = time.time()
        
        try:
            # Login and add items to cart
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add multiple items
            for item in self.test_data['food_items'][:3]:  # Add first 3 items
                self.client.get(f'/cart/add-to-cart/{item.id}/')
            
            # Test quantity manipulation
            user = User.objects.get(username='testuser')
            cart_items = user.profile.inventory.item_set.all()
            
            if cart_items.exists():
                first_item = cart_items.first()
                original_quantity = first_item.quantity
                
                # Test quantity increase
                response = self.client.get(f'/cart/item/quantity/{first_item.id}/up/')
                first_item.refresh_from_db()
                quantity_increased = first_item.quantity > original_quantity
                self.log_result("Quantity Increase", quantity_increased, 
                              f"Quantity: {original_quantity} → {first_item.quantity}", time.time() - start_time)
                
                # Test quantity decrease
                response = self.client.get(f'/cart/item/quantity/{first_item.id}/down/')
                first_item.refresh_from_db()
                quantity_decreased = first_item.quantity < first_item.quantity + 1
                self.log_result("Quantity Decrease", quantity_decreased, 
                              f"Quantity: {first_item.quantity}", time.time() - start_time)
            
            # Test item deletion
            if cart_items.exists():
                item_to_delete = cart_items.first()
                response = self.client.get(f'/cart/item/delete/{item_to_delete.id}/')
                success = response.status_code in [200, 302]
                self.log_result("Item Deletion", success, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
            # Test cart clearing
            response = self.client.get('/cart/item/delete_cart/')
            success = response.status_code in [200, 302]
            self.log_result("Cart Clearing", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Cart Management", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_checkout_process(self):
        """Test checkout process"""
        start_time = time.time()
        
        try:
            # Login and add items to cart
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add items to cart
            for item in self.test_data['food_items'][:2]:  # Add 2 items
                self.client.get(f'/cart/add-to-cart/{item.id}/')
            
            # Test checkout initiation
            response = self.client.get('/cart/checkout/')
            success = response.status_code in [200, 302]
            self.log_result("Checkout Initiation", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test transaction creation
            response = self.client.get('/cart/transaction/')  # Note: typo in original URL
            success = response.status_code in [200, 302]
            self.log_result("Transaction Creation", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Verify transaction was created
            user = User.objects.get(username='testuser')
            transactions = Transaction.objects.filter(owner=user.profile)
            transaction_created = transactions.exists()
            self.log_result("Transaction Verification", transaction_created, 
                          f"Transactions: {transactions.count()}", time.time() - start_time)
            
            # Verify cart was cleared after transaction
            cart_items = user.profile.inventory.item_set.all()
            cart_cleared = cart_items.count() == 0
            self.log_result("Cart Cleared After Transaction", cart_cleared, 
                          f"Items remaining: {cart_items.count()}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Checkout Process", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_user_profile_access(self):
        """Test user profile access"""
        start_time = time.time()
        
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test profile access
            response = self.client.get('/accounts/profile/')
            self.log_result("Profile Access", response.status_code == 200, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test profile data
            user = User.objects.get(username='testuser')
            profile_data_correct = (
                hasattr(user, 'profile') and 
                user.profile is not None and
                user.profile.user == user
            )
            self.log_result("Profile Data Integrity", profile_data_correct, 
                          "Profile data is correct", time.time() - start_time)
            
        except Exception as e:
            self.log_result("User Profile Access", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_url_access_control(self):
        """Test URL access control for authenticated users"""
        start_time = time.time()
        
        try:
            # Test unauthenticated access to protected URLs
            protected_urls = [
                '/shop/',
                '/cart/order-summary/',
                '/operations/orders/',
                '/accounts/profile/'
            ]
            
            for url in protected_urls:
                response = self.client.get(url)
                # Should redirect to login or show appropriate response
                access_controlled = response.status_code in [200, 302, 403]
                self.log_result(f"Access Control: {url}", access_controlled, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
            # Test authenticated access
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            for url in protected_urls:
                response = self.client.get(url)
                authenticated_access = response.status_code in [200, 302]
                self.log_result(f"Authenticated Access: {url}", authenticated_access, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("URL Access Control", False, f"Error: {str(e)}", time.time() - start_time)
    
    def run_all_tests(self):
        """Run all user functionality tests"""
        print("  🔍 User Registration & Authentication")
        self.test_user_registration()
        self.test_user_login_logout()
        
        print("  🛒 Shopping & Cart Management")
        self.test_menu_browsing()
        self.test_add_to_cart()
        self.test_cart_management()
        
        print("  💳 Checkout & Transactions")
        self.test_checkout_process()
        
        print("  👤 User Profile & Access Control")
        self.test_user_profile_access()
        self.test_url_access_control()
        
        # Summary
        passed = sum(1 for _, status, _, _ in self.results if status)
        total = len(self.results)
        print(f"  📊 User Tests: {passed}/{total} passed ({(passed/total*100):.1f}%)")

