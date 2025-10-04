#!/bin/bash

# olgFeast Setup Script
# This script sets up all dependencies and prepares the application for first run

set -e

echo "🔧 Setting up olgFeast Restaurant Management System"
echo "=================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✅ Python $PYTHON_VERSION found"
else
    echo "❌ Python 3.13+ is required"
    echo "Please install Python 3.13 or later"
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    echo "✅ Node.js $NODE_VERSION found"
else
    echo "❌ Node.js 18+ is required"
    echo "Please install Node.js 18 or later"
    exit 1
fi

# Check npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm $NPM_VERSION found"
else
    echo "❌ npm is required"
    exit 1
fi

# Setup backend
echo ""
echo "🐍 Setting up Python backend..."
cd fastapi_app

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt

echo "✅ Backend setup complete"

# Go back to root
cd ..

# Setup frontend
echo ""
echo "🎨 Setting up React frontend..."
cd frontend

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install -q

echo "✅ Frontend setup complete"

# Go back to root
cd ..

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating environment configuration..."
    cp env.example .env
    echo "✅ Environment file created with default settings"
fi

# Make scripts executable
echo ""
echo "🔧 Making scripts executable..."
chmod +x run.sh
chmod +x stop.sh
chmod +x deploy.sh

echo ""
echo "🎉 Setup complete!"
echo "=================================================="
echo ""
echo "🚀 Ready to run! Execute:"
echo "   ./run.sh"
echo ""
echo "📖 The application will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "👤 Demo Credentials:"
echo "   Staff: admin / admin123"
echo "   Customer: customer / customer123"
echo "=================================================="
