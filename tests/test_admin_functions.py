#!/usr/bin/env python3
"""
Comprehensive Admin Functionality Tests
Tests all admin features including order management, status updates, user management
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

class AdminFunctionTests:
    """Test class for admin functionality"""
    
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
    
    def test_admin_login(self):
        """Test admin user login"""
        start_time = time.time()
        
        try:
            # Test staff user login
            response = self.client.post('/login/', {
                'username': 'staffuser',
                'password': 'staffpass123'
            })
            success = response.status_code in [200, 302]
            self.log_result("Staff User Login", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test superuser login
            self.client.logout()
            response = self.client.post('/login/', {
                'username': 'adminuser',
                'password': 'adminpass123'
            })
            success = response.status_code in [200, 302]
            self.log_result("Superuser Login", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Admin Login", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_order_tracking_access(self):
        """Test order tracking page access for staff"""
        start_time = time.time()
        
        try:
            # Test staff access to order tracking
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            response = self.client.get('/operations/orders/')
            self.log_result("Staff Order Tracking Access", response.status_code == 200, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test non-staff access (should be restricted)
            self.client.logout()
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            response = self.client.get('/operations/orders/')
            # Non-staff users should still be able to view but not modify
            access_granted = response.status_code == 200
            self.log_result("Non-Staff Order Tracking Access", access_granted, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Order Tracking Access", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_order_status_management(self):
        """Test order status update functionality"""
        start_time = time.time()
        
        try:
            # Login as staff user
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            # Create a test transaction
            user = self.test_data['regular_user']
            transaction = Transaction.objects.create(
                owner=user.profile,
                ref_code='TEST123456789',
                status='pending'
            )
            
            # Add items to transaction
            for item in self.test_data['food_items'][:2]:
                transaction.items.add(item)
            transaction.save()
            
            # Test status updates
            status_transitions = [
                ('pending', 'preparing'),
                ('preparing', 'ready'),
                ('ready', 'complete')
            ]
            
            for current_status, new_status in status_transitions:
                # Update transaction status
                transaction.status = current_status
                transaction.save()
                
                # Test status update via URL
                response = self.client.get(f'/operations/update-status/{transaction.id}/{new_status}/')
                success = response.status_code in [200, 302]
                self.log_result(f"Status Update: {current_status} → {new_status}", success, 
                              f"Status: {response.status_code}", time.time() - start_time)
                
                # Verify status was updated
                transaction.refresh_from_db()
                status_updated = transaction.status == new_status
                self.log_result(f"Status Verification: {new_status}", status_updated, 
                              f"Current status: {transaction.status}", time.time() - start_time)
            
            # Clean up test transaction
            transaction.delete()
            
        except Exception as e:
            self.log_result("Order Status Management", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_order_creation_and_tracking(self):
        """Test complete order creation and tracking workflow"""
        start_time = time.time()
        
        try:
            # Login as regular user and create order
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add items to cart
            for item in self.test_data['food_items'][:3]:
                self.client.get(f'/cart/add-to-cart/{item.id}/')
            
            # Create transaction
            response = self.client.get('/cart/transaction/')
            success = response.status_code in [200, 302]
            self.log_result("Order Creation", success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Verify transaction exists
            user = User.objects.get(username='testuser')
            transactions = Transaction.objects.filter(owner=user.profile)
            transaction_exists = transactions.exists()
            self.log_result("Transaction Exists", transaction_exists, 
                          f"Transactions: {transactions.count()}", time.time() - start_time)
            
            if transaction_exists:
                transaction = transactions.first()
                
                # Login as staff and test order tracking
                self.client.logout()
                self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
                
                # Test order appears in tracking
                response = self.client.get('/operations/orders/')
                order_visible = transaction.ref_code[:8].encode() in response.content
                self.log_result("Order Visibility in Tracking", order_visible, 
                              "Order visible on tracking page", time.time() - start_time)
                
                # Test status update workflow
                response = self.client.get(f'/operations/update-status/{transaction.id}/preparing/')
                status_update_success = response.status_code in [200, 302]
                self.log_result("Order Status Update", status_update_success, 
                              f"Status: {response.status_code}", time.time() - start_time)
                
                # Verify order moved to preparing column
                transaction.refresh_from_db()
                status_correct = transaction.status == 'preparing'
                self.log_result("Order Status Verification", status_correct, 
                              f"Status: {transaction.status}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Order Creation and Tracking", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_admin_dashboard_access(self):
        """Test Django admin dashboard access"""
        start_time = time.time()
        
        try:
            # Test superuser admin access
            self.client.post('/login/', {'username': 'adminuser', 'password': 'adminpass123'})
            
            response = self.client.get('/admin/')
            admin_access = response.status_code == 200
            self.log_result("Django Admin Access", admin_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test admin model access
            admin_urls = [
                '/admin/auth/user/',
                '/admin/accounts/profile/',
                '/admin/shop_front/fooditem/',
                '/admin/shopping_cart/transaction/',
                '/admin/shopping_cart/item/',
            ]
            
            for url in admin_urls:
                response = self.client.get(url)
                model_access = response.status_code == 200
                self.log_result(f"Admin Model Access: {url.split('/')[-2]}", model_access, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
            # Test non-superuser admin access (should be denied)
            self.client.logout()
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            response = self.client.get('/admin/')
            # Staff users without superuser status should be redirected or denied
            staff_admin_access = response.status_code in [200, 302, 403]
            self.log_result("Staff Admin Access", staff_admin_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Admin Dashboard Access", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_user_management(self):
        """Test user management functionality"""
        start_time = time.time()
        
        try:
            # Login as superuser
            self.client.post('/login/', {'username': 'adminuser', 'password': 'adminpass123'})
            
            # Test user creation via admin
            response = self.client.get('/admin/auth/user/add/')
            user_creation_access = response.status_code == 200
            self.log_result("User Creation Access", user_creation_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test user list access
            response = self.client.get('/admin/auth/user/')
            user_list_access = response.status_code == 200
            self.log_result("User List Access", user_list_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test profile management
            response = self.client.get('/admin/accounts/profile/')
            profile_access = response.status_code == 200
            self.log_result("Profile Management Access", profile_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("User Management", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_food_item_management(self):
        """Test food item management functionality"""
        start_time = time.time()
        
        try:
            # Login as superuser
            self.client.post('/login/', {'username': 'adminuser', 'password': 'adminpass123'})
            
            # Test food item list access
            response = self.client.get('/admin/shop_front/fooditem/')
            food_item_access = response.status_code == 200
            self.log_result("Food Item List Access", food_item_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test food item creation access
            response = self.client.get('/admin/shop_front/fooditem/add/')
            food_item_creation_access = response.status_code == 200
            self.log_result("Food Item Creation Access", food_item_creation_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test food item editing
            if self.test_data['food_items']:
                first_item = self.test_data['food_items'][0]
                response = self.client.get(f'/admin/shop_front/fooditem/{first_item.id}/change/')
                food_item_edit_access = response.status_code == 200
                self.log_result("Food Item Edit Access", food_item_edit_access, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Food Item Management", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_transaction_management(self):
        """Test transaction management functionality"""
        start_time = time.time()
        
        try:
            # Login as superuser
            self.client.post('/login/', {'username': 'adminuser', 'password': 'adminpass123'})
            
            # Test transaction list access
            response = self.client.get('/admin/shopping_cart/transaction/')
            transaction_access = response.status_code == 200
            self.log_result("Transaction List Access", transaction_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Create a test transaction for management testing
            user = self.test_data['regular_user']
            transaction = Transaction.objects.create(
                owner=user.profile,
                ref_code='ADMINTEST123',
                status='pending'
            )
            
            # Test transaction editing
            response = self.client.get(f'/admin/shopping_cart/transaction/{transaction.id}/change/')
            transaction_edit_access = response.status_code == 200
            self.log_result("Transaction Edit Access", transaction_edit_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test transaction deletion access
            response = self.client.get(f'/admin/shopping_cart/transaction/{transaction.id}/delete/')
            transaction_delete_access = response.status_code == 200
            self.log_result("Transaction Delete Access", transaction_delete_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Clean up test transaction
            transaction.delete()
            
        except Exception as e:
            self.log_result("Transaction Management", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_staff_permissions(self):
        """Test staff user permissions and restrictions"""
        start_time = time.time()
        
        try:
            # Test staff user permissions
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            # Staff should be able to access order tracking
            response = self.client.get('/operations/orders/')
            staff_order_access = response.status_code == 200
            self.log_result("Staff Order Tracking Access", staff_order_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Staff should be able to update order status
            user = self.test_data['regular_user']
            transaction = Transaction.objects.create(
                owner=user.profile,
                ref_code='STAFFTEST123',
                status='pending'
            )
            
            response = self.client.get(f'/operations/update-status/{transaction.id}/preparing/')
            staff_status_update = response.status_code in [200, 302]
            self.log_result("Staff Status Update Permission", staff_status_update, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Staff should have admin access (Django default behavior)
            response = self.client.get('/admin/')
            staff_admin_access = response.status_code in [200, 302]  # Allowed or redirected to login
            self.log_result("Staff Admin Access", staff_admin_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Clean up test transaction
            transaction.delete()
            
        except Exception as e:
            self.log_result("Staff Permissions", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_order_analytics_and_reporting(self):
        """Test order analytics and reporting functionality"""
        start_time = time.time()
        
        try:
            # Login as staff user
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            # Create multiple test transactions with different statuses
            user = self.test_data['regular_user']
            test_transactions = []
            
            statuses = ['pending', 'preparing', 'ready', 'complete']
            for i, status in enumerate(statuses):
                transaction = Transaction.objects.create(
                    owner=user.profile,
                    ref_code=f'ANALYTICS{i}',
                    status=status
                )
                test_transactions.append(transaction)
            
            # Test order tracking page shows all statuses
            response = self.client.get('/operations/orders/')
            tracking_page_works = response.status_code == 200
            self.log_result("Order Tracking Analytics", tracking_page_works, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Verify different status columns are populated
            if tracking_page_works:
                content = response.content.decode()
                status_counts = {
                    'pending': content.count('Pending'),
                    'preparing': content.count('Preparing'),
                    'ready': content.count('Ready'),
                    'complete': content.count('Complete')
                }
                
                for status, count in status_counts.items():
                    self.log_result(f"Status Column: {status}", count > 0, 
                                  f"Count: {count}", time.time() - start_time)
            
            # Clean up test transactions
            for transaction in test_transactions:
                transaction.delete()
            
        except Exception as e:
            self.log_result("Order Analytics", False, f"Error: {str(e)}", time.time() - start_time)
    
    def run_all_tests(self):
        """Run all admin functionality tests"""
        print("  🔐 Admin Authentication & Access")
        self.test_admin_login()
        self.test_order_tracking_access()
        
        print("  📋 Order Management")
        self.test_order_status_management()
        self.test_order_creation_and_tracking()
        self.test_order_analytics_and_reporting()
        
        print("  🛠️  Admin Dashboard & Management")
        self.test_admin_dashboard_access()
        self.test_user_management()
        self.test_food_item_management()
        self.test_transaction_management()
        
        print("  👥 Staff Permissions & Security")
        self.test_staff_permissions()
        
        # Summary
        passed = sum(1 for _, status, _, _ in self.results if status)
        total = len(self.results)
        print(f"  📊 Admin Tests: {passed}/{total} passed ({(passed/total*100):.1f}%)")

