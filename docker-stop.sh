#!/bin/bash

# olgFeast Docker Stop Script
# This script stops all application services

set -e

echo "🛑 Stopping olgFeast Application..."

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

# Stop services
print_status "Stopping Docker services..."
docker-compose down

print_success "All services stopped successfully! ✓"

echo ""
echo "📋 Optional cleanup commands:"
echo "  • Remove volumes (data): docker-compose down -v"
echo "  • Remove images: docker-compose down --rmi all"
echo "  • Full cleanup: docker-compose down -v --rmi all"
echo ""
echo "⚠️  Warning: Removing volumes will delete all database data!"
