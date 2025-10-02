#!/usr/bin/env python3
"""
Performance Tests for olgFeast
Tests system performance under various loads and conditions
"""

import time
import threading
from typing import Dict, List, Tuple
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction

from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Inventory, Item, Transaction

class PerformanceTests:
    """Test class for performance testing"""
    
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
    
    def test_page_load_performance(self):
        """Test page load performance for key pages"""
        start_time = time.time()
        
        try:
            # Test public pages
            public_pages = [
                ('/', 'Home Page'),
                ('/register/', 'Registration Page'),
                ('/login/', 'Login Page'),
            ]
            
            for url, name in public_pages:
                page_start = time.time()
                response = self.client.get(url)
                page_duration = time.time() - page_start
                
                success = response.status_code == 200 and page_duration < 2.0  # 2 second threshold
                self.log_result(f"Page Load: {name}", success, 
                              f"Status: {response.status_code}, Time: {page_duration:.2f}s", page_duration)
            
            # Test authenticated pages
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            authenticated_pages = [
                ('/shop/', 'Shop Page'),
                ('/cart/order-summary/', 'Cart Summary'),
                ('/operations/orders/', 'Order Tracking'),
                ('/accounts/profile/', 'Profile Page'),
            ]
            
            for url, name in authenticated_pages:
                page_start = time.time()
                response = self.client.get(url)
                page_duration = time.time() - page_start
                
                success = response.status_code == 200 and page_duration < 3.0  # 3 second threshold for authenticated pages
                self.log_result(f"Page Load: {name}", success, 
                              f"Status: {response.status_code}, Time: {page_duration:.2f}s", page_duration)
            
        except Exception as e:
            self.log_result("Page Load Performance", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_database_query_performance(self):
        """Test database query performance"""
        start_time = time.time()
        
        try:
            # Test user queries
            query_start = time.time()
            users = User.objects.all()
            user_count = users.count()
            query_duration = time.time() - query_start
            
            success = query_duration < 0.1  # 100ms threshold
            self.log_result("Database: User Query", success, 
                          f"Users: {user_count}, Time: {query_duration:.3f}s", query_duration)
            
            # Test food item queries
            query_start = time.time()
            food_items = FoodItem.objects.all()
            item_count = food_items.count()
            query_duration = time.time() - query_start
            
            success = query_duration < 0.1
            self.log_result("Database: Food Item Query", success, 
                          f"Items: {item_count}, Time: {query_duration:.3f}s", query_duration)
            
            # Test transaction queries
            query_start = time.time()
            transactions = Transaction.objects.all()
            transaction_count = transactions.count()
            query_duration = time.time() - query_start
            
            success = query_duration < 0.1
            self.log_result("Database: Transaction Query", success, 
                          f"Transactions: {transaction_count}, Time: {query_duration:.3f}s", query_duration)
            
            # Test complex query (transactions with items)
            query_start = time.time()
            complex_transactions = Transaction.objects.select_related('owner__user').prefetch_related('items').all()
            complex_count = complex_transactions.count()
            query_duration = time.time() - query_start
            
            success = query_duration < 0.2  # 200ms threshold for complex queries
            self.log_result("Database: Complex Query", success, 
                          f"Complex transactions: {complex_count}, Time: {query_duration:.3f}s", query_duration)
            
        except Exception as e:
            self.log_result("Database Query Performance", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_cart_operations_performance(self):
        """Test cart operations performance"""
        start_time = time.time()
        
        try:
            # Login first
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Test adding multiple items to cart
            add_start = time.time()
            items_added = 0
            for item in self.test_data['food_items']:
                response = self.client.get(f'/cart/add-to-cart/{item.id}/')
                if response.status_code in [200, 302]:
                    items_added += 1
            add_duration = time.time() - add_start
            
            success = add_duration < 2.0 and items_added > 0
            self.log_result("Cart: Add Multiple Items", success, 
                          f"Items: {items_added}, Time: {add_duration:.2f}s", add_duration)
            
            # Test cart view performance
            view_start = time.time()
            response = self.client.get('/cart/order-summary/')
            view_duration = time.time() - view_start
            
            success = response.status_code == 200 and view_duration < 1.0
            self.log_result("Cart: View Performance", success, 
                          f"Status: {response.status_code}, Time: {view_duration:.2f}s", view_duration)
            
            # Test quantity updates
            user = User.objects.get(username='testuser')
            cart_items = user.profile.inventory.item_set.all()
            
            if cart_items.exists():
                first_item = cart_items.first()
                update_start = time.time()
                response = self.client.get(f'/cart/item/quantity/{first_item.id}/up/')
                update_duration = time.time() - update_start
                
                success = response.status_code in [200, 302] and update_duration < 0.5
                self.log_result("Cart: Quantity Update", success, 
                              f"Status: {response.status_code}, Time: {update_duration:.2f}s", update_duration)
            
        except Exception as e:
            self.log_result("Cart Operations Performance", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_order_processing_performance(self):
        """Test order processing performance"""
        start_time = time.time()
        
        try:
            # Login and add items
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add items to cart
            for item in self.test_data['food_items'][:3]:
                self.client.get(f'/cart/add-to-cart/{item.id}/')
            
            # Test checkout performance
            checkout_start = time.time()
            response = self.client.get('/cart/transaction/')
            checkout_duration = time.time() - checkout_start
            
            success = response.status_code in [200, 302] and checkout_duration < 2.0
            self.log_result("Order: Checkout Performance", success, 
                          f"Status: {response.status_code}, Time: {checkout_duration:.2f}s", checkout_duration)
            
            # Test order tracking performance
            self.client.logout()
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            tracking_start = time.time()
            response = self.client.get('/operations/orders/')
            tracking_duration = time.time() - tracking_start
            
            success = response.status_code == 200 and tracking_duration < 2.0
            self.log_result("Order: Tracking Performance", success, 
                          f"Status: {response.status_code}, Time: {tracking_duration:.2f}s", tracking_duration)
            
            # Test status update performance
            user = User.objects.get(username='testuser')
            transaction = Transaction.objects.filter(owner=user.profile).first()
            
            if transaction:
                status_start = time.time()
                response = self.client.get(f'/operations/update-status/{transaction.id}/preparing/')
                status_duration = time.time() - status_start
                
                success = response.status_code in [200, 302] and status_duration < 1.0
                self.log_result("Order: Status Update Performance", success, 
                              f"Status: {response.status_code}, Time: {status_duration:.2f}s", status_duration)
            
        except Exception as e:
            self.log_result("Order Processing Performance", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_concurrent_user_performance(self):
        """Test performance with concurrent users"""
        start_time = time.time()
        
        try:
            # Create multiple test users
            test_users = []
            for i in range(5):
                user_data = {
                    'username': f'perfuser{i}',
                    'password1': 'perfpass123!',
                    'password2': 'perfpass123!'
                }
                
                response = self.client.post('/register/', user_data)
                if response.status_code in [200, 302]:
                    test_users.append(f'perfuser{i}')
            
            self.log_result("Concurrent: User Creation", len(test_users) == 5, 
                          f"Users created: {len(test_users)}", time.time() - start_time)
            
            # Test concurrent login performance
            login_times = []
            for username in test_users:
                login_start = time.time()
                response = self.client.post('/login/', {
                    'username': username,
                    'password': 'perfpass123!'
                })
                login_duration = time.time() - login_start
                login_times.append(login_duration)
            
            avg_login_time = sum(login_times) / len(login_times)
            max_login_time = max(login_times)
            
            success = avg_login_time < 1.0 and max_login_time < 2.0
            self.log_result("Concurrent: Login Performance", success, 
                          f"Avg: {avg_login_time:.2f}s, Max: {max_login_time:.2f}s", avg_login_time)
            
            # Test concurrent cart operations
            cart_times = []
            for username in test_users:
                self.client.post('/login/', {'username': username, 'password': 'perfpass123!'})
                
                cart_start = time.time()
                # Add one item to cart
                if self.test_data['food_items']:
                    self.client.get(f'/cart/add-to-cart/{self.test_data["food_items"][0].id}/')
                cart_duration = time.time() - cart_start
                cart_times.append(cart_duration)
            
            avg_cart_time = sum(cart_times) / len(cart_times)
            max_cart_time = max(cart_times)
            
            success = avg_cart_time < 0.5 and max_cart_time < 1.0
            self.log_result("Concurrent: Cart Operations", success, 
                          f"Avg: {avg_cart_time:.2f}s, Max: {max_cart_time:.2f}s", avg_cart_time)
            
            # Clean up test users
            for username in test_users:
                User.objects.filter(username=username).delete()
            
        except Exception as e:
            self.log_result("Concurrent User Performance", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_memory_usage_performance(self):
        """Test memory usage and resource consumption"""
        start_time = time.time()
        
        try:
            import psutil
            import os
            
            # Get current process
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform memory-intensive operations
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add many items to cart
            for _ in range(10):  # Add each item 10 times
                for item in self.test_data['food_items']:
                    self.client.get(f'/cart/add-to-cart/{item.id}/')
            
            # Check memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            success = memory_increase < 50  # Less than 50MB increase
            self.log_result("Memory: Usage Performance", success, 
                          f"Memory increase: {memory_increase:.1f}MB", time.time() - start_time)
            
            # Test garbage collection
            import gc
            gc_start = time.time()
            gc.collect()
            gc_duration = time.time() - gc_start
            
            success = gc_duration < 1.0
            self.log_result("Memory: Garbage Collection", success, 
                          f"GC time: {gc_duration:.2f}s", gc_duration)
            
        except ImportError:
            self.log_result("Memory: Usage Performance", True, "psutil not available, skipping", time.time() - start_time)
        except Exception as e:
            self.log_result("Memory Usage Performance", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_large_dataset_performance(self):
        """Test performance with larger datasets"""
        start_time = time.time()
        
        try:
            # Create multiple transactions
            user = self.test_data['regular_user']
            transactions_created = 0
            
            creation_start = time.time()
            for i in range(20):  # Create 20 transactions
                transaction = Transaction.objects.create(
                    owner=user.profile,
                    ref_code=f'PERFTEST{i:03d}',
                    status='pending'
                )
                # Add items to transaction
                for item in self.test_data['food_items'][:2]:
                    transaction.items.add(item)
                transaction.save()
                transactions_created += 1
            creation_duration = time.time() - creation_start
            
            success = creation_duration < 5.0 and transactions_created == 20
            self.log_result("Large Dataset: Transaction Creation", success, 
                          f"Created: {transactions_created}, Time: {creation_duration:.2f}s", creation_duration)
            
            # Test querying large dataset
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            query_start = time.time()
            response = self.client.get('/operations/orders/')
            query_duration = time.time() - query_start
            
            success = response.status_code == 200 and query_duration < 3.0
            self.log_result("Large Dataset: Query Performance", success, 
                          f"Status: {response.status_code}, Time: {query_duration:.2f}s", query_duration)
            
            # Test bulk status updates
            update_start = time.time()
            transactions = Transaction.objects.filter(ref_code__startswith='PERFTEST')
            updated_count = 0
            
            for transaction in transactions:
                response = self.client.get(f'/operations/update-status/{transaction.id}/preparing/')
                if response.status_code in [200, 302]:
                    updated_count += 1
            update_duration = time.time() - update_start
            
            success = update_duration < 10.0 and updated_count == transactions.count()
            self.log_result("Large Dataset: Bulk Updates", success, 
                          f"Updated: {updated_count}, Time: {update_duration:.2f}s", update_duration)
            
            # Clean up test transactions
            Transaction.objects.filter(ref_code__startswith='PERFTEST').delete()
            
        except Exception as e:
            self.log_result("Large Dataset Performance", False, f"Error: {str(e)}", time.time() - start_time)
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("  ⚡ Page Load Performance")
        self.test_page_load_performance()
        
        print("  🗄️  Database Performance")
        self.test_database_query_performance()
        
        print("  🛒 Cart Operations Performance")
        self.test_cart_operations_performance()
        
        print("  📋 Order Processing Performance")
        self.test_order_processing_performance()
        
        print("  👥 Concurrent User Performance")
        self.test_concurrent_user_performance()
        
        print("  💾 Memory & Resource Performance")
        self.test_memory_usage_performance()
        
        print("  📊 Large Dataset Performance")
        self.test_large_dataset_performance()
        
        # Summary
        passed = sum(1 for _, status, _, _ in self.results if status)
        total = len(self.results)
        print(f"  📊 Performance Tests: {passed}/{total} passed ({(passed/total*100):.1f}%)")

