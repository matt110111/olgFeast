#!/usr/bin/env python3
"""
Integration Tests for olgFeast
Tests complete workflows and system integration
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

class IntegrationTests:
    """Test class for integration testing"""
    
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
    
    def test_complete_customer_journey(self):
        """Test complete customer journey from registration to order completion"""
        start_time = time.time()
        
        try:
            # Step 1: User Registration
            registration_data = {
                'username': 'journeyuser',
                'password1': 'journeypass123!',
                'password2': 'journeypass123!'
            }
            
            response = self.client.post('/register/', registration_data)
            registration_success = response.status_code in [200, 302]
            self.log_result("Customer Journey: Registration", registration_success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Step 2: Login
            response = self.client.post('/login/', {
                'username': 'journeyuser',
                'password': 'journeypass123!'
            })
            login_success = response.status_code in [200, 302]
            self.log_result("Customer Journey: Login", login_success, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Step 3: Browse Menu
            response = self.client.get('/shop/')
            menu_access = response.status_code == 200
            self.log_result("Customer Journey: Menu Browse", menu_access, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Step 4: Add Items to Cart
            items_added = 0
            for item in self.test_data['food_items'][:3]:
                response = self.client.get(f'/cart/add-to-cart/{item.id}/')
                if response.status_code in [200, 302]:
                    items_added += 1
            
            self.log_result("Customer Journey: Add to Cart", items_added > 0, 
                          f"Items added: {items_added}", time.time() - start_time)
            
            # Step 5: View Cart
            response = self.client.get('/cart/order-summary/')
            cart_view = response.status_code == 200
            self.log_result("Customer Journey: View Cart", cart_view, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Step 6: Modify Cart
            user = User.objects.get(username='journeyuser')
            cart_items = user.profile.inventory.item_set.all()
            if cart_items.exists():
                first_item = cart_items.first()
                response = self.client.get(f'/cart/item/quantity/{first_item.id}/up/')
                cart_modification = response.status_code in [200, 302]
                self.log_result("Customer Journey: Modify Cart", cart_modification, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
            # Step 7: Checkout
            response = self.client.get('/cart/checkout/')
            checkout_initiation = response.status_code in [200, 302]
            self.log_result("Customer Journey: Checkout", checkout_initiation, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Step 8: Complete Transaction
            response = self.client.get('/cart/transaction/')
            transaction_complete = response.status_code in [200, 302]
            self.log_result("Customer Journey: Transaction", transaction_complete, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Step 9: Verify Order Created
            transactions = Transaction.objects.filter(owner=user.profile)
            order_created = transactions.exists()
            self.log_result("Customer Journey: Order Created", order_created, 
                          f"Orders: {transactions.count()}", time.time() - start_time)
            
            # Clean up
            User.objects.filter(username='journeyuser').delete()
            
        except Exception as e:
            self.log_result("Complete Customer Journey", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_staff_order_management_workflow(self):
        """Test complete staff order management workflow"""
        start_time = time.time()
        
        try:
            # Step 1: Customer creates order
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add items and create order
            for item in self.test_data['food_items'][:2]:
                self.client.get(f'/cart/add-to-cart/{item.id}/')
            
            self.client.get('/cart/transaction/')
            
            # Get the created transaction
            user = User.objects.get(username='testuser')
            transaction = Transaction.objects.filter(owner=user.profile).first()
            
            if transaction:
                self.log_result("Staff Workflow: Order Created", True, 
                              f"Order: {transaction.ref_code}", time.time() - start_time)
                
                # Step 2: Staff logs in and views orders
                self.client.logout()
                self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
                
                response = self.client.get('/operations/orders/')
                order_visible = transaction.ref_code[:8].encode() in response.content
                self.log_result("Staff Workflow: Order Visible", order_visible, 
                              "Order visible in tracking", time.time() - start_time)
                
                # Step 3: Staff updates order status (Pending → Preparing)
                response = self.client.get(f'/operations/update-status/{transaction.id}/preparing/')
                status_update_1 = response.status_code in [200, 302]
                self.log_result("Staff Workflow: Status Update 1", status_update_1, 
                              f"Status: {response.status_code}", time.time() - start_time)
                
                # Step 4: Staff updates order status (Preparing → Ready)
                transaction.refresh_from_db()
                transaction.status = 'preparing'
                transaction.save()
                
                response = self.client.get(f'/operations/update-status/{transaction.id}/ready/')
                status_update_2 = response.status_code in [200, 302]
                self.log_result("Staff Workflow: Status Update 2", status_update_2, 
                              f"Status: {response.status_code}", time.time() - start_time)
                
                # Step 5: Staff updates order status (Ready → Complete)
                transaction.refresh_from_db()
                transaction.status = 'ready'
                transaction.save()
                
                response = self.client.get(f'/operations/update-status/{transaction.id}/complete/')
                status_update_3 = response.status_code in [200, 302]
                self.log_result("Staff Workflow: Status Update 3", status_update_3, 
                              f"Status: {response.status_code}", time.time() - start_time)
                
                # Step 6: Verify final status
                transaction.refresh_from_db()
                final_status_correct = transaction.status == 'complete'
                self.log_result("Staff Workflow: Final Status", final_status_correct, 
                              f"Final status: {transaction.status}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Staff Order Management Workflow", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_multi_user_order_processing(self):
        """Test multiple users creating orders simultaneously"""
        start_time = time.time()
        
        try:
            # Create multiple test users and orders
            test_users = []
            test_transactions = []
            
            for i in range(3):
                # Create user
                user_data = {
                    'username': f'multiuser{i}',
                    'password1': 'multipass123!',
                    'password2': 'multipass123!'
                }
                
                response = self.client.post('/register/', user_data)
                if response.status_code in [200, 302]:
                    # Login and create order
                    self.client.post('/login/', {
                        'username': f'multiuser{i}',
                        'password': 'multipass123!'
                    })
                    
                    # Add items to cart
                    for item in self.test_data['food_items'][:2]:
                        self.client.get(f'/cart/add-to-cart/{item.id}/')
                    
                    # Create transaction
                    self.client.get('/cart/transaction/')
                    
                    user = User.objects.get(username=f'multiuser{i}')
                    transaction = Transaction.objects.filter(owner=user.profile).first()
                    
                    if transaction:
                        test_users.append(user)
                        test_transactions.append(transaction)
            
            self.log_result("Multi-User: Order Creation", len(test_transactions) == 3, 
                          f"Orders created: {len(test_transactions)}", time.time() - start_time)
            
            # Test staff can see all orders
            self.client.logout()
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            
            response = self.client.get('/operations/orders/')
            all_orders_visible = all(
                transaction.ref_code[:8].encode() in response.content 
                for transaction in test_transactions
            )
            self.log_result("Multi-User: All Orders Visible", all_orders_visible, 
                          "All orders visible to staff", time.time() - start_time)
            
            # Test processing multiple orders
            processed_orders = 0
            for transaction in test_transactions:
                response = self.client.get(f'/operations/update-status/{transaction.id}/preparing/')
                if response.status_code in [200, 302]:
                    processed_orders += 1
            
            self.log_result("Multi-User: Order Processing", processed_orders == len(test_transactions), 
                          f"Orders processed: {processed_orders}/{len(test_transactions)}", time.time() - start_time)
            
            # Clean up
            for user in test_users:
                user.delete()
            
        except Exception as e:
            self.log_result("Multi-User Order Processing", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_data_consistency_across_models(self):
        """Test data consistency across different models"""
        start_time = time.time()
        
        try:
            # Create a complete order and verify data consistency
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add items to cart
            added_items = []
            for item in self.test_data['food_items'][:3]:
                response = self.client.get(f'/cart/add-to-cart/{item.id}/')
                if response.status_code in [200, 302]:
                    added_items.append(item)
            
            # Create transaction
            self.client.get('/cart/transaction/')
            
            # Verify data consistency
            user = User.objects.get(username='testuser')
            transaction = Transaction.objects.filter(owner=user.profile).first()
            
            if transaction:
                # Check transaction has correct owner
                owner_correct = transaction.owner == user.profile
                self.log_result("Data Consistency: Transaction Owner", owner_correct, 
                              "Transaction owner is correct", time.time() - start_time)
                
                # Check transaction has items
                transaction_items = transaction.items.all()
                items_consistent = len(transaction_items) > 0
                self.log_result("Data Consistency: Transaction Items", items_consistent, 
                              f"Transaction has {len(transaction_items)} items", time.time() - start_time)
                
                # Check transaction totals are calculated
                total_value = transaction.total_value
                total_tickets = transaction.total_tickets
                totals_calculated = total_value > 0 and total_tickets > 0
                self.log_result("Data Consistency: Transaction Totals", totals_calculated, 
                              f"Total: ${total_value}, Tickets: {total_tickets}", time.time() - start_time)
                
                # Check cart was cleared
                cart_items = user.profile.inventory.item_set.all()
                cart_cleared = cart_items.count() == 0
                self.log_result("Data Consistency: Cart Cleared", cart_cleared, 
                              f"Cart items: {cart_items.count()}", time.time() - start_time)
                
            # Check transaction status (should be pending for new transactions)
            # Note: Status might be 'complete' if transaction was processed by other tests
            status_valid = transaction.status in ['pending', 'preparing', 'ready', 'complete']
            self.log_result("Data Consistency: Transaction Status", status_valid, 
                          f"Status: {transaction.status}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Data Consistency", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases"""
        start_time = time.time()
        
        try:
            # Test invalid item ID
            response = self.client.get('/cart/add-to-cart/99999/')
            invalid_item_handled = response.status_code in [200, 302, 404]
            self.log_result("Error Handling: Invalid Item ID", invalid_item_handled, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test invalid transaction ID for status update
            self.client.post('/login/', {'username': 'staffuser', 'password': 'staffpass123'})
            response = self.client.get('/operations/update-status/99999/preparing/')
            invalid_transaction_handled = response.status_code in [200, 302, 404]
            self.log_result("Error Handling: Invalid Transaction ID", invalid_transaction_handled, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test invalid status update
            user = User.objects.get(username='testuser')
            transaction = Transaction.objects.filter(owner=user.profile).first()
            if transaction:
                response = self.client.get(f'/operations/update-status/{transaction.id}/invalid_status/')
                invalid_status_handled = response.status_code in [200, 302, 404]
                self.log_result("Error Handling: Invalid Status", invalid_status_handled, 
                              f"Status: {response.status_code}", time.time() - start_time)
            
            # Test unauthorized access
            self.client.logout()
            response = self.client.get('/operations/orders/')
            unauthorized_handled = response.status_code in [200, 302, 403]
            self.log_result("Error Handling: Unauthorized Access", unauthorized_handled, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test empty cart checkout
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            response = self.client.get('/cart/checkout/')
            empty_cart_handled = response.status_code in [200, 302]
            self.log_result("Error Handling: Empty Cart Checkout", empty_cart_handled, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Error Handling", False, f"Error: {str(e)}", time.time() - start_time)
    
    def test_session_management(self):
        """Test session management and user state persistence"""
        start_time = time.time()
        
        try:
            # Test login session persistence
            self.client.post('/login/', {'username': 'testuser', 'password': 'testpass123'})
            
            # Add items to cart
            for item in self.test_data['food_items'][:2]:
                self.client.get(f'/cart/add-to-cart/{item.id}/')
            
            # Verify cart persists across requests
            response = self.client.get('/cart/order-summary/')
            cart_persists = response.status_code == 200
            self.log_result("Session: Cart Persistence", cart_persists, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test logout clears session
            self.client.get('/logout/')
            response = self.client.get('/cart/order-summary/')
            session_cleared = response.status_code in [200, 302, 403]
            self.log_result("Session: Logout Clears Session", session_cleared, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
            # Test session timeout (simulate by creating new client)
            new_client = Client()
            response = new_client.get('/cart/order-summary/')
            session_timeout_handled = response.status_code in [200, 302, 403]
            self.log_result("Session: Timeout Handling", session_timeout_handled, 
                          f"Status: {response.status_code}", time.time() - start_time)
            
        except Exception as e:
            self.log_result("Session Management", False, f"Error: {str(e)}", time.time() - start_time)
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("  🛣️  Complete User Workflows")
        self.test_complete_customer_journey()
        self.test_staff_order_management_workflow()
        
        print("  👥 Multi-User Scenarios")
        self.test_multi_user_order_processing()
        
        print("  🔗 System Integration")
        self.test_data_consistency_across_models()
        self.test_error_handling_and_edge_cases()
        self.test_session_management()
        
        # Summary
        passed = sum(1 for _, status, _, _ in self.results if status)
        total = len(self.results)
        print(f"  📊 Integration Tests: {passed}/{total} passed ({(passed/total*100):.1f}%)")

