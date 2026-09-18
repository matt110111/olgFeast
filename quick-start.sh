#!/bin/bash

# Quick start script for olgFeast
echo "🍽️  Starting olgFeast Application..."
echo "=================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start the application
echo "🚀 Launching application..."
./docker-start.sh

echo ""
echo "✅ Application started!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop: ./docker-stop.sh"
echo "For development: ./docker-dev.sh"
