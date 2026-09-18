#!/bin/bash
cd "$(dirname "$0")/frontend"

echo "🚀 Starting olgFeast Frontend Server..."
echo "📁 Working directory: $(pwd)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "🌐 Starting React development server on http://localhost:3000"
echo "🌍 Network access: http://192.168.3.125:3000"
echo "Press Ctrl+C to stop"
echo "=" * 50

# Start the frontend server
npm start
