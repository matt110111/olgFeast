#!/bin/bash

# olgFeast Deployment Script
# This script handles deployment of the full-stack application

set -e

echo "🚀 Starting olgFeast Deployment"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Environment setup
ENV=${1:-development}
echo "📋 Environment: $ENV"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "⚠️  Please update .env file with your configuration before running again."
    exit 1
fi

# Build and start services
echo "🏗️  Building and starting services..."

if [ "$ENV" = "production" ]; then
    echo "🔧 Production deployment mode"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
else
    echo "🔧 Development deployment mode"
    docker-compose up -d --build
fi

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs backend
    exit 1
fi

# Check frontend
if curl -f http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose logs frontend
    exit 1
fi

# Run database migrations (if needed)
echo "🗄️  Running database migrations..."
docker-compose exec backend python -c "
from app.core.database import engine, Base
from app.models import user, menu, cart, order
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"

# Seed initial data (if needed)
echo "🌱 Seeding initial data..."
docker-compose exec backend python seed_data.py

echo "=================================================="
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Admin Panel: http://localhost:8000/admin"
echo ""
echo "📊 Demo Credentials:"
echo "   Staff: admin / admin123"
echo "   Customer: customer / customer123"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update services: docker-compose up -d --build"
echo "=================================================="
