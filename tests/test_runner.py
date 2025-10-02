#!/usr/bin/env python3
"""
Comprehensive Test Runner for olgFeast
Runs all test suites and provides detailed reporting
"""

import os
import sys
import django
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db import transaction
from django.core.management import call_command

from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Inventory, Item, Transaction

class TestRunner:
    """Main test runner class"""
    
    def __init__(self):
        self.client = Client()
        self.results = []
        self.start_time = None
        self.end_time = None
        self.test_data = {}
        
    def log_result(self, test_name: str, status: bool, message: str = "", duration: float = 0):
        """Log test results with timing"""
        status_symbol = "✅" if status else "❌"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        result = f"{status_symbol} {test_name}{duration_str}"
        if message:
            result += f" - {message}"
        print(result)
        self.results.append((test_name, status, message, duration))
    
    def setup_test_data(self):
        """Create comprehensive test data"""
        print("🔧 Setting up test data...")
        
        # Create test users
        self.test_data['regular_user'] = self._create_user('testuser', 'test@example.com', 'testpass123', is_staff=False)
        self.test_data['staff_user'] = self._create_user('staffuser', 'staff@example.com', 'staffpass123', is_staff=True)
        self.test_data['admin_user'] = self._create_user('adminuser', 'admin@example.com', 'adminpass123', is_staff=True, is_superuser=True)
        
        # Create test food items
        self.test_data['food_items'] = self._create_food_items()
        
        print("✅ Test data setup complete")
    
    def _create_user(self, username: str, email: str, password: str, is_staff: bool = False, is_superuser: bool = False) -> User:
        """Create a test user"""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
                'is_active': True
            }
        )
        if created:
            user.set_password(password)
            user.save()
            
            # Create profile
            profile, _ = Profile.objects.get_or_create(user=user)
            if not profile.inventory:
                inventory = Inventory.objects.create()
                profile.inventory = inventory
                profile.save()
        
        return user
    
    def _create_food_items(self) -> List[FoodItem]:
        """Create test food items"""
        items_data = [
            {'name': 'Test Burger', 'food_group': 'Main Course', 'value': 12.99, 'ticket': 1},
            {'name': 'Test Pizza', 'food_group': 'Main Course', 'value': 15.99, 'ticket': 2},
            {'name': 'Test Salad', 'food_group': 'Appetizer', 'value': 8.99, 'ticket': 1},
            {'name': 'Test Drink', 'food_group': 'Beverage', 'value': 3.99, 'ticket': 1},
            {'name': 'Test Dessert', 'food_group': 'Dessert', 'value': 6.99, 'ticket': 1},
        ]
        
        items = []
        for item_data in items_data:
            item, created = FoodItem.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            items.append(item)
        
        return items
    
    def run_user_tests(self):
        """Run comprehensive user functionality tests"""
        print("\n🧪 Running User Functionality Tests")
        print("=" * 50)
        
        # Import and run user tests
        from .test_user_functions import UserFunctionTests
        user_tests = UserFunctionTests(self.client, self.test_data)
        user_tests.run_all_tests()
        self.results.extend(user_tests.results)
    
    def run_admin_tests(self):
        """Run comprehensive admin functionality tests"""
        print("\n👨‍💼 Running Admin Functionality Tests")
        print("=" * 50)
        
        # Import and run admin tests
        from .test_admin_functions import AdminFunctionTests
        admin_tests = AdminFunctionTests(self.client, self.test_data)
        admin_tests.run_all_tests()
        self.results.extend(admin_tests.results)
    
    def run_integration_tests(self):
        """Run integration tests"""
        print("\n🔗 Running Integration Tests")
        print("=" * 50)
        
        # Import and run integration tests
        from .test_integration import IntegrationTests
        integration_tests = IntegrationTests(self.client, self.test_data)
        integration_tests.run_all_tests()
        self.results.extend(integration_tests.results)
    
    def run_performance_tests(self):
        """Run performance tests"""
        print("\n⚡ Running Performance Tests")
        print("=" * 50)
        
        # Import and run performance tests
        from .test_performance import PerformanceTests
        performance_tests = PerformanceTests(self.client, self.test_data)
        performance_tests.run_all_tests()
        self.results.extend(performance_tests.results)
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test transactions
        Transaction.objects.filter(owner__user__username__in=['testuser', 'staffuser', 'adminuser']).delete()
        
        # Delete test items from inventories
        for username in ['testuser', 'staffuser', 'adminuser']:
            try:
                user = User.objects.get(username=username)
                if user.profile.inventory:
                    user.profile.inventory.item_set.all().delete()
            except User.DoesNotExist:
                pass
        
        # Delete test users
        User.objects.filter(username__in=['testuser', 'staffuser', 'adminuser']).delete()
        
        print("✅ Test data cleanup complete")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        print(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Total Tests: {len(self.results)}")
        
        # Count results
        passed = sum(1 for _, status, _, _ in self.results if status)
        failed = len(self.results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%" if self.results else "0%")
        
        # Show failed tests
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, status, message, duration in self.results:
                if not status:
                    print(f"  • {test_name}: {message}")
        
        # Performance summary
        total_test_time = sum(duration for _, _, _, duration in self.results)
        print(f"\n⏱️  Total Test Time: {total_test_time:.2f}s")
        print(f"⏱️  Setup/Cleanup Time: {total_duration - total_test_time:.2f}s")
        
        return {
            'total_tests': len(self.results),
            'passed': passed,
            'failed': failed,
            'success_rate': (passed/len(self.results)*100) if self.results else 0,
            'total_duration': total_duration,
            'results': self.results
        }
    
    def run_all_tests(self):
        """Run all test suites"""
        self.start_time = time.time()
        
        print("🚀 Starting Comprehensive olgFeast Test Suite")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_data()
            
            # Run test suites
            self.run_user_tests()
            self.run_admin_tests()
            self.run_integration_tests()
            self.run_performance_tests()
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            self.cleanup_test_data()
            
            # Generate report
            report = self.generate_report()
            
            # Exit with appropriate code
            if report['failed'] > 0:
                sys.exit(1)
            else:
                sys.exit(0)

def main():
    """Main entry point"""
    runner = TestRunner()
    runner.run_all_tests()

if __name__ == '__main__':
    main()

