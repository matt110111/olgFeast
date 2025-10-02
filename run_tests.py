#!/usr/bin/env python3
"""
Simple Test Runner for olgFeast
Quick script to run Django tests and comprehensive tests
"""

import os
import sys
import django
import subprocess

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
django.setup()

def run_django_tests():
    """Run Django's built-in test suite"""
    print("🧪 Running Django Test Suite")
    print("=" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'test', '--verbosity=2'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running Django tests: {e}")
        return False

def run_comprehensive_tests():
    """Run comprehensive test suite"""
    print("\n🚀 Running Comprehensive Test Suite")
    print("=" * 40)
    
    try:
        from tests.test_runner import TestRunner
        runner = TestRunner()
        runner.run_all_tests()
        return True
    except Exception as e:
        print(f"Error running comprehensive tests: {e}")
        return False

def main():
    """Main entry point"""
    print("🍽️ olgFeast Test Suite Runner")
    print("=" * 50)
    
    # Run Django tests
    django_success = run_django_tests()
    
    # Run comprehensive tests
    comprehensive_success = run_comprehensive_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Django Tests: {'✅ PASSED' if django_success else '❌ FAILED'}")
    print(f"Comprehensive Tests: {'✅ PASSED' if comprehensive_success else '❌ FAILED'}")
    
    if django_success and comprehensive_success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

