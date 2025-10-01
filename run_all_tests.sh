#!/bin/bash
# olgFeast Test Runner Script
# Runs all tests to validate site functionality

echo "🧪 olgFeast Comprehensive Test Suite"
echo "=================================="

# Set up environment
export PATH="/home/zeeker/Documents/olgFeast/venv/bin:$PATH"
cd /home/zeeker/Documents/olgFeast

echo ""
echo "📋 Running Quick Functionality Test..."
echo "--------------------------------------"
python quick_test.py

echo ""
echo "📋 Running Django Unit Tests..."
echo "--------------------------------"
python manage.py test shopping_cart.tests

echo ""
echo "📋 Running All Django Tests..."
echo "------------------------------"
python manage.py test

echo ""
echo "🎉 Test Suite Complete!"
echo "Check results above for any failures."
