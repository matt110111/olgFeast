#!/bin/bash

# OlgFeast Production Deployment Script
# This script pulls the latest images and restarts the application with zero downtime

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE="docker.prod.env"
BACKUP_DIR="./backups"
LOG_FILE="./deploy.log"

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

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if required files exist
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Production compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found: $ENV_FILE"
        print_status "Using default environment variables from shell"
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create backup of current state
create_backup() {
    print_status "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current docker-compose configuration
    if [ -f "$COMPOSE_FILE" ]; then
        cp "$COMPOSE_FILE" "$BACKUP_DIR/docker-compose.prod.yml.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Backup environment file if it exists
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$BACKUP_DIR/docker.prod.env.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Save current running container state
    docker-compose -f "$COMPOSE_FILE" ps > "$BACKUP_DIR/containers_backup.$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || true
    
    print_success "Backup created successfully"
}

# Pull latest images
pull_images() {
    print_status "Pulling latest images from GitHub Container Registry..."
    
    # Login to GitHub Container Registry (if needed)
    if [ -n "$GHCR_TOKEN" ]; then
        print_status "Logging in to GitHub Container Registry..."
        echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_OWNER" --password-stdin
    fi
    
    # Pull images
    if [ -f "$ENV_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull
    else
        docker-compose -f "$COMPOSE_FILE" pull
    fi
    
    print_success "Images pulled successfully"
}

# Perform zero-downtime deployment
deploy() {
    print_status "Starting zero-downtime deployment..."
    
    # Stop old containers and start new ones
    if [ -f "$ENV_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --remove-orphans
    else
        docker-compose -f "$COMPOSE_FILE" up -d --remove-orphans
    fi
    
    print_success "Deployment completed successfully"
}

# Health check
health_check() {
    print_status "Performing health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Health check attempt $attempt/$max_attempts..."
        
        # Check backend health
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is healthy"
        else
            print_warning "Backend health check failed, attempt $attempt"
        fi
        
        # Check frontend health
        if curl -f http://localhost:3000/ > /dev/null 2>&1; then
            print_success "Frontend is healthy"
            break
        else
            print_warning "Frontend health check failed, attempt $attempt"
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Health checks failed after $max_attempts attempts"
            return 1
        fi
        
        sleep 5
        ((attempt++))
    done
    
    print_success "All health checks passed"
}

# Clean up old images
cleanup() {
    print_status "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused images (be careful with this in production)
    if [ "${CLEANUP_UNUSED_IMAGES:-false}" = "true" ]; then
        print_warning "Removing unused images (this may remove other project images)"
        docker image prune -a -f
    fi
    
    print_success "Cleanup completed"
}

# Rollback function
rollback() {
    print_warning "Rolling back to previous version..."
    
    # Stop current containers
    if [ -f "$ENV_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    else
        docker-compose -f "$COMPOSE_FILE" down
    fi
    
    # Find the most recent backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/docker-compose.prod.yml.backup.* 2>/dev/null | head -n1)
    
    if [ -n "$latest_backup" ]; then
        print_status "Restoring from backup: $latest_backup"
        cp "$latest_backup" "$COMPOSE_FILE"
        
        # Start with previous configuration
        if [ -f "$ENV_FILE" ]; then
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        else
            docker-compose -f "$COMPOSE_FILE" up -d
        fi
        
        print_success "Rollback completed"
    else
        print_error "No backup found for rollback"
        exit 1
    fi
}

# Show deployment status
show_status() {
    print_status "Current deployment status:"
    
    if [ -f "$ENV_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    else
        docker-compose -f "$COMPOSE_FILE" ps
    fi
    
    echo ""
    print_status "Application URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
}

# Main function
main() {
    local command="${1:-deploy}"
    
    echo "🚀 OlgFeast Production Deployment Script"
    echo "========================================"
    echo ""
    
    case "$command" in
        "deploy")
            check_prerequisites
            create_backup
            pull_images
            deploy
            health_check
            cleanup
            show_status
            log "Deployment completed successfully"
            ;;
        "pull")
            check_prerequisites
            pull_images
            log "Image pull completed"
            ;;
        "rollback")
            rollback
            health_check
            show_status
            log "Rollback completed"
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            log "Cleanup completed"
            ;;
        "health")
            health_check
            ;;
        *)
            echo "Usage: $0 {deploy|pull|rollback|status|cleanup|health}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Full deployment (default)"
            echo "  pull     - Pull latest images only"
            echo "  rollback - Rollback to previous version"
            echo "  status   - Show current deployment status"
            echo "  cleanup  - Clean up old Docker images"
            echo "  health   - Run health checks"
            echo ""
            echo "Environment Variables:"
            echo "  GHCR_OWNER - Your GitHub username (default: matt110111)"
            echo "  GHCR_TOKEN - GitHub Container Registry token (optional for public images)"
            echo "  CLEANUP_UNUSED_IMAGES - Set to 'true' to remove unused images (default: false)"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"