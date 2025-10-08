#!/bin/bash

# olgFeast Simple Run Script (No port checking)
# This script starts the application without complex port management

set -e

echo "🚀 Starting olgFeast Restaurant Management System"
echo "=================================================="

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "✅ .env file created with default settings"
fi

# Start backend
echo "🔧 Starting FastAPI Backend..."
cd fastapi_app

# Activate virtual environment
source venv/bin/activate

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

# Save PID for cleanup
echo $BACKEND_PID > ../.backend.pid

# Go back to root directory
cd ..

# Start frontend
echo "🎨 Starting React Frontend..."
cd frontend

# Load Node.js environment
export NVM_DIR="$HOME/.config/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Start frontend in background
echo "🚀 Starting React development server..."
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started with PID: $FRONTEND_PID"

# Save PID for cleanup
echo $FRONTEND_PID > ../.frontend.pid

# Go back to root directory
cd ..

echo ""
echo "🎉 olgFeast is starting up!"
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

# Keep script running
echo "📋 Services are starting up..."
echo "Press Ctrl+C to stop all services"

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
    
    echo "✅ All services stopped"
    exit 0
}

# Set trap for cleanup on script exit
trap cleanup INT TERM

# Wait for user to stop
wait
