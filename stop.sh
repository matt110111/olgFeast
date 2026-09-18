#!/bin/bash

# olgFeast Stop Script
# This script cleanly stops all running services

echo "🛑 Stopping olgFeast Restaurant Management System"
echo "=================================================="

# Function to kill processes on port
kill_port() {
    local port=$1
    
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$pids" ]; then
            echo "🔧 Stopping processes on port $port..."
            echo $pids | xargs kill -9 2>/dev/null || true
        fi
    elif command -v fuser >/dev/null 2>&1; then
        echo "🔧 Stopping processes on port $port..."
        fuser -k $port/tcp 2>/dev/null || true
    else
        echo "⚠️  Cannot automatically kill processes on port $port"
        echo "Please manually stop any processes using port $port"
    fi
}

# Stop backend if PID file exists
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "🔧 Stopping FastAPI backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    rm -f .backend.pid
fi

# Stop frontend if PID file exists
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "🔧 Stopping React frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f .frontend.pid
fi

# Kill any remaining processes on ports
kill_port 8000
kill_port 3000

# Wait a moment for processes to stop
sleep 2

# Final check and cleanup
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

if check_port 8000; then
    echo "⚠️  Backend still running on port 8000"
else
    echo "✅ Backend stopped"
fi

if check_port 3000; then
    echo "⚠️  Frontend still running on port 3000"
else
    echo "✅ Frontend stopped"
fi

echo "=================================================="
echo "✅ All olgFeast services have been stopped"
