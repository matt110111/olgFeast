#!/bin/bash

# olgFeast Docker Development Script
# This script starts the application in development mode with hot reloading

set -e

echo "🔧 Starting olgFeast in Development Mode..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Create development environment file
if [ ! -f .env ]; then
    print_status "Creating development .env file..."
    cat > .env << EOF
# Development Environment Configuration
DATABASE_URL=postgresql://olgfeast:olgfeast_password@db:5432/olgfeast
REDIS_URL=redis://:redis_password@redis:6379
SECRET_KEY=dev-secret-key-not-for-production
DEBUG=true
ENVIRONMENT=development
EOF
fi

# Build and start services in development mode
print_status "Building development Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env build

print_status "Starting development services..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env up -d db redis

# Wait for database and Redis to be ready
print_status "Waiting for database and Redis to start..."
sleep 15

# Start backend with hot reload
print_status "Starting backend with hot reload..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env up backend &

# Start frontend with hot reload
print_status "Starting frontend with hot reload..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env up frontend &

# Wait for services to start
sleep 10

print_success "Development environment started! 🎉"
echo ""
echo "📱 Frontend (Hot Reload): http://localhost:3000"
echo "🔧 Backend API (Hot Reload): http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "📋 Development commands:"
echo "  • View logs: docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f"
echo "  • Stop services: docker-compose -f docker-compose.yml -f docker-compose.override.yml down"
echo "  • Restart backend: docker-compose -f docker-compose.yml -f docker-compose.override.yml restart backend"
echo "  • Restart frontend: docker-compose -f docker-compose.yml -f docker-compose.override.yml restart frontend"
echo ""
print_warning "Files are mounted for hot reloading. Changes will be reflected automatically!"

# Keep script running and show logs
echo "Press Ctrl+C to stop all services..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env logs -f
