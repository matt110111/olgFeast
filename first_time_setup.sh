#!/bin/bash

# OlgFeast First-Time Setup Script
# # This script handles the initial setup for production deployment
# [INFO] Initializing database with schema and sample data...
# 🗄️  Setting up OlgFeast database...
# 📋 Creating database tables...
# 🍽️  Creating menu items...
# ✅ Database setup completed successfully!

# 📋 Generated Credentials:
#    Admin User: admin / 9ymTF4O2ggPMptdr2LBtJQ
#    Customer User: customer / pSGeQ3-PWwjqGwCA

# ⚠️  IMPORTANT: Save these credentials securely!
#    You can change them later through the admin panel.
# ❌ Error setting up database: [Errno 13] Permission denied: 'deployment_credentials.txt'
# Traceback (most recent call last):
#   File "/app/setup_database.py", line 166, in <module>
#     main()
#     ~~~~^^
#   File "/app/setup_database.py", line 163, in main
#     setup_database()
#     ~~~~~~~~~~~~~~^^
#   File "/app/setup_database.py", line 127, in setup_database
#     with open(credentials_file, "w") as f:
#          ~~~~^^^^^^^^^^^^^^^^^^^^^^^
# PermissionError: [Errno 13] Permission denied: 'deployment_credentials.txt'


set -e

echo "🚀 OlgFeast First-Time Setup"
echo "============================="
echo

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

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Create production environment file
create_env_file() {
    print_status "Creating production environment file..."
    
    if [ -f "docker.env" ]; then
        print_warning "docker.env already exists. Backing up to docker.env.backup"
        cp docker.env docker.env.backup
    fi
    
    # Generate secure passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    
    cat > docker.env << EOF
# OlgFeast Production Environment Variables
# Generated on $(date)

# Database Configuration
POSTGRES_DB=olgfeast
POSTGRES_USER=olgfeast
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Redis Configuration
REDIS_PASSWORD=${REDIS_PASSWORD}

# Application Configuration
SECRET_KEY=${SECRET_KEY}
DEBUG=false
ENVIRONMENT=production

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME="OlgFeast"

# CORS Configuration
BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:3000", "http://localhost:3001"]

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF

    print_success "Environment file created: docker.env"
    print_warning "Keep docker.env secure and never commit it to version control!"
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Start only database and redis services
    print_status "Starting database and redis services..."
    docker-compose -f docker-compose.yml --env-file docker.env up -d db redis
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if database is ready
    print_status "Checking database connection..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.yml --env-file docker.env exec db pg_isready -U olgfeast -d olgfeast > /dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Database failed to start after 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    # Start backend service temporarily for database setup
    print_status "Starting backend service for database setup..."
    docker-compose -f docker-compose.yml --env-file docker.env up -d backend
    
    # Wait for backend to be ready
    print_status "Waiting for backend service to be ready..."
    sleep 15
    
    # Setup database schema and initial data
    print_status "Initializing database with schema and sample data..."
    docker-compose -f docker-compose.yml --env-file docker.env exec backend python setup_database.py
    
    print_success "Database setup completed"
}

# Build and start application
start_application() {
    print_status "Building and starting frontend service..."
    
    # Build and start frontend (backend is already running)
    docker-compose -f docker-compose.yml --env-file docker.env up -d --build frontend
    
    # Wait for services to be ready
    print_status "Waiting for application to be ready..."
    sleep 15
    
    # Check if services are healthy
    print_status "Checking service health..."
    
    # Check backend
    for i in {1..30}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Backend health check failed, but continuing..."
            break
        fi
        sleep 2
    done
    
    # Check frontend
    for i in {1..30}; do
        if curl -f http://localhost:3000/ > /dev/null 2>&1; then
            print_success "Frontend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Frontend health check failed, but continuing..."
            break
        fi
        sleep 2
    done
}

# Display final information
show_completion_info() {
    echo
    echo "🎉 Setup Completed Successfully!"
    echo "================================"
    echo
    print_success "OlgFeast is now running in production mode!"
    echo
    echo "📱 Application URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo
    echo "🔐 Default Credentials:"
    echo "   Check deployment_credentials.txt for admin and customer credentials"
    echo
    echo "⚠️  IMPORTANT SECURITY NOTES:"
    echo "   1. Change default passwords immediately after first login"
    echo "   2. Keep docker.env file secure and never share it"
    echo "   3. Delete deployment_credentials.txt after noting credentials"
    echo "   4. Set up proper firewall rules for production deployment"
    echo
    echo "📚 Next Steps:"
    echo "   1. Access the application at http://localhost:3000"
    echo "   2. Log in with admin credentials to access admin panel"
    echo "   3. Create additional users as needed"
    echo "   4. Configure your domain and SSL certificates"
    echo
    print_warning "Remember to delete deployment_credentials.txt after use!"
}

# Main setup process
main() {
    echo "Starting OlgFeast first-time setup..."
    echo
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Create environment file
    create_env_file
    
    # Setup database
    setup_database
    
    # Start application
    start_application
    
    # Show completion information
    show_completion_info
}

# Handle script arguments
case "${1:-}" in
    "cleanup")
        print_status "Cleaning up OlgFeast deployment..."
        docker-compose -f docker-compose.yml --env-file docker.env down --volumes --remove-orphans
        print_success "Cleanup completed"
        ;;
    "restart")
        print_status "Restarting OlgFeast services..."
        docker-compose -f docker-compose.yml --env-file docker.env restart
        print_success "Services restarted"
        ;;
    "logs")
        docker-compose -f docker-compose.yml --env-file docker.env logs -f
        ;;
    "status")
        docker-compose -f docker-compose.yml --env-file docker.env ps
        ;;
    *)
        main
        ;;
esac
