#!/bin/bash

# olgFeast Simple Run Script
# This script makes it super simple to run the full application

set -e

echo "🚀 Starting olgFeast Restaurant Management System"
echo "=================================================="

# Function to check if port is in use
check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0  # Port is in use
        else
            return 1  # Port is free
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -ln | grep ":$port " >/dev/null 2>&1; then
            return 0  # Port is in use
        else
            return 1  # Port is free
        fi
    else
        # Fallback: try to connect to the port
        if timeout 1 bash -c "</dev/tcp/localhost/$port" 2>/dev/null; then
            return 0  # Port is in use
        else
            return 1  # Port is free
        fi
    fi
}

# Function to kill processes on port
kill_port() {
    local port=$1
    echo "🔧 Stopping processes on port $port..."
    
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    elif command -v fuser >/dev/null 2>&1; then
        fuser -k $port/tcp 2>/dev/null || true
    else
        echo "⚠️  Cannot automatically kill processes on port $port"
        echo "Please manually stop any processes using port $port"
    fi
    
    sleep 2
}

# Check and handle port conflicts
if check_port 8000; then
    echo "⚠️  Port 8000 is already in use. Stopping existing processes..."
    kill_port 8000
fi

if check_port 3000; then
    echo "⚠️  Port 3000 is already in use. Stopping existing processes..."
    kill_port 3000
fi

# Setup environment
echo "📋 Setting up environment..."

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "✅ .env file created with default settings"
fi

# Navigate to backend directory
echo "🔧 Starting FastAPI Backend..."
cd fastapi_app

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt

# Setup database if needed
if [ ! -f "fastapi_olgfeast.db" ]; then
    echo "🗄️  Setting up database..."
    python setup_database.py
fi

# Start backend in background
echo "🚀 Starting FastAPI server..."
python start_dev.py &
BACKEND_PID=$!
echo "✅ Backend started with PID: $BACKEND_PID"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if check_port 8000; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Failed to start backend"
    exit 1
fi

# Go back to root directory
cd ..

# Start frontend
echo "🎨 Starting React Frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install -q
fi

# Start frontend in background
echo "🚀 Starting React development server..."
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started with PID: $FRONTEND_PID"

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 10

# Go back to root directory
cd ..

# Check if frontend is running
if check_port 3000; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "❌ Failed to start frontend"
    exit 1
fi

# Save PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "🎉 olgFeast is now running!"
echo "=================================================="
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "👤 Demo Credentials:"
echo "   Staff: admin / admin123"
echo "   Customer: customer / customer123"
echo ""
echo "🛑 To stop the application, run: ./stop.sh"
echo "=================================================="

# Keep script running and show logs
echo "📋 Showing logs (Ctrl+C to stop all services)..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    
    if [ -f .backend.pid ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm -f .backend.pid
    fi
    
    if [ -f .frontend.pid ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm -f .frontend.pid
    fi
    
    # Kill any remaining processes
    kill_port 8000
    kill_port 3000
    
    echo "✅ All services stopped"
    exit 0
}

# Set trap for cleanup on script exit
trap cleanup INT TERM

# Wait for user to stop
wait
