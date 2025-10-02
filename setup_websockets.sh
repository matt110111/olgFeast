#!/bin/bash

# Setup script for WebSocket functionality in olgFeast
# This script installs Redis and the required Python packages

echo "🍽️  Setting up WebSocket functionality for olgFeast Kitchen Display..."

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "📦 Installing Redis..."
    
    # Detect OS and install Redis accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            echo "❌ Homebrew not found. Please install Redis manually:"
            echo "   Visit: https://redis.io/download"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y redis-server
        elif command -v yum &> /dev/null; then
            sudo yum install -y redis
        else
            echo "❌ Package manager not found. Please install Redis manually:"
            echo "   Visit: https://redis.io/download"
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install Redis manually:"
        echo "   Visit: https://redis.io/download"
        exit 1
    fi
else
    echo "✅ Redis is already installed"
fi

# Start Redis service
echo "🚀 Starting Redis service..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start redis
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start redis
    sudo systemctl enable redis
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found. Installing globally..."
fi

pip install channels==4.0.0 channels-redis==4.2.0

echo "✅ WebSocket setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Make sure Redis is running: redis-cli ping"
echo "2. Run migrations: python manage.py migrate"
echo "3. Start the server: python manage.py runserver"
echo "4. For production, use: daphne -b 0.0.0.0 -p 8000 olgFeast.asgi:application"
echo ""
echo "🌐 WebSocket endpoints:"
echo "   - Kitchen displays: ws://localhost:8000/ws/kitchen/{station}/"
echo "   - Stations: pending, preparing, ready"
echo ""
echo "📱 Test the kitchen display:"
echo "   - Navigate to: http://localhost:8000/operations/stations/"
echo "   - Open a station display in a new tab"
echo "   - Create an order to see real-time updates!"
