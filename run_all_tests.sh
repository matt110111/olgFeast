#!/bin/bash
# Comprehensive Test Runner for olgFeast

echo "🍽️ olgFeast Comprehensive Test Suite"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run comprehensive test suite
echo "🚀 Running comprehensive test suite..."
python run_tests.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed successfully!"
    echo "✅ olgFeast is ready for production!"
else
    echo ""
    echo "❌ Some tests failed. Please check the output above."
    exit 1
fi
