#!/bin/bash

# olgFeast Docker Deployment Script
# This script starts the entire application using Docker Compose

set -e

echo "🚀 Starting olgFeast Application with Docker..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker and Docker Compose are available ✓"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Check if .env file exists, if not create from docker.env
if [ ! -f .env ]; then
    print_warning ".env file not found, creating from docker.env..."
    cp docker.env .env
    print_warning "Please review and update .env file with your production settings!"
fi

# Build and start services
print_status "Building Docker images..."
docker-compose build

print_status "Starting services..."
docker-compose up -d

# Wait for services to be healthy
print_status "Waiting for services to start..."
sleep 10

# Check service health
print_status "Checking service health..."

# Check database
if docker-compose ps db | grep -q "healthy"; then
    print_success "Database is healthy ✓"
else
    print_warning "Database health check failed, but continuing..."
fi

# Check Redis
if docker-compose ps redis | grep -q "healthy"; then
    print_success "Redis is healthy ✓"
else
    print_warning "Redis health check failed, but continuing..."
fi

# Run database migrations
print_status "Running database migrations..."
docker-compose exec -T backend alembic upgrade head

print_success "Application started successfully! 🎉"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🗄️ Database: localhost:5432"
echo "🔄 Redis: localhost:6379"
echo ""
echo "📋 Useful commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Restart services: docker-compose restart"
echo "  • View service status: docker-compose ps"
echo ""
print_warning "Remember to update your .env file with production settings!"
