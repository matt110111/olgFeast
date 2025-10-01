#!/usr/bin/env python3
"""
Site Functionality Test Runner
Uses Django's test framework to validate site functionality
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def main():
    """Run Django tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run tests for specific apps
    failures = test_runner.run_tests([
        "accounts.tests",
        "shop_front.tests", 
        "shopping_cart.tests",
        "users.tests"
    ])
    
    if failures:
        print(f"❌ {failures} test(s) failed")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
