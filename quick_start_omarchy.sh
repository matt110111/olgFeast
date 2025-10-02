#!/bin/bash

# 🍽️ olgFeast - Quick Start Script for Omarchy (Development Mode)
# This script quickly sets up olgFeast for development on Omarchy

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

main() {
    print_header "🍽️ olgFeast - Quick Start for Omarchy"
    
    # Check if we're in the right directory
    if [[ ! -f "manage.py" ]]; then
        print_error "manage.py not found! Please run this script from the olgFeast project root."
        exit 1
    fi
    
    print_status "Installing essential packages..."
    sudo pacman -S --noconfirm python python-pip python-virtualenv redis
    
    print_status "Starting Redis service..."
    sudo systemctl start redis
    sudo systemctl enable redis
    
    print_status "Creating virtual environment..."
    if [[ -d "venv_omarchy" ]]; then
        rm -rf venv_omarchy
    fi
    python -m venv venv_omarchy
    source venv_omarchy/bin/activate
    
    print_status "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Setting up database..."
    python manage.py makemigrations
    python manage.py migrate
    
    print_status "Collecting static files..."
    python manage.py collectstatic --noinput
    
    print_header "🎉 Quick Setup Complete!"
    echo -e "${GREEN}olgFeast is ready to run!${NC}"
    echo ""
    echo -e "${CYAN}To start the development server:${NC}"
    echo -e "  ${BLUE}source venv_omarchy/bin/activate${NC}"
    echo -e "  ${BLUE}python manage.py runserver 0.0.0.0:8000${NC}"
    echo ""
    echo -e "${CYAN}Access your application at:${NC}"
    echo -e "  🌐 http://localhost:8000"
    echo -e "  🔧 http://localhost:8000/admin"
    echo ""
    echo -e "${YELLOW}Redis is running for WebSocket functionality ✓${NC}"
    echo ""
    echo -e "${GREEN}Would you like to start the server now? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Starting development server..."
        python manage.py runserver 0.0.0.0:8000
    else
        print_status "Setup complete! Run the commands above when ready."
    fi
}

main "$@"
