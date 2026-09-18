#!/bin/bash
cd "$(dirname "$0")/fastapi_app"

echo "🚀 Starting olgFeast Backend Server..."
echo "📁 Working directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🌐 Starting FastAPI server on http://127.0.0.1:8000"
echo "📖 Local API Documentation: http://127.0.0.1:8000/docs"
echo "🏥 Local Health Check: http://127.0.0.1:8000/health"
echo "🌍 Network access: http://192.168.3.125:8000"
echo "📖 Network API Documentation: http://192.168.3.125:8000/docs"
echo "Press Ctrl+C to stop"
echo "=" * 50

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
