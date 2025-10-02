#!/usr/bin/env python3
"""
Comprehensive Test Runner for olgFeast
Simple script to run all test suites
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
django.setup()

from tests.test_runner import TestRunner

def main():
    """Main entry point for running comprehensive tests"""
    print("🚀 olgFeast Comprehensive Test Suite")
    print("=" * 50)
    
    runner = TestRunner()
    runner.run_all_tests()

if __name__ == '__main__':
    main()

