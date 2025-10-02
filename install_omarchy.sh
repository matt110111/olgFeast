#!/bin/bash

# 🍽️ olgFeast - Complete Omarchy Installation Script
# This script installs and configures olgFeast on a fresh Omarchy system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if user is root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root!"
        print_warning "Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Function to check if we're on Arch Linux/Omarchy
check_arch() {
    if ! command_exists pacman; then
        print_error "This script is designed for Arch Linux/Omarchy systems."
        print_error "pacman package manager not found."
        exit 1
    fi
    print_status "Detected Arch Linux/Omarchy system ✓"
}

# Function to update system
update_system() {
    print_header "🔄 Updating System Packages"
    print_status "Updating package database and system..."
    sudo pacman -Syu --noconfirm
    print_status "System updated successfully ✓"
}

# Function to install required packages
install_packages() {
    print_header "📦 Installing Required Packages"
    
    local packages=(
        "python"
        "python-pip"
        "python-virtualenv"
        "git"
        "sqlite"
        "redis"
        "nginx"
        "gunicorn"
        "nodejs"
        "npm"
    )
    
    print_status "Installing packages: ${packages[*]}"
    sudo pacman -S --noconfirm "${packages[@]}"
    print_status "All packages installed successfully ✓"
}

# Function to start and enable services
setup_services() {
    print_header "🔧 Setting Up Services"
    
    print_status "Starting and enabling Redis service..."
    sudo systemctl start redis
    sudo systemctl enable redis
    
    print_status "Starting and enabling Nginx service..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    print_status "Services configured successfully ✓"
}

# Function to create project directory
setup_project_directory() {
    print_header "📁 Setting Up Project Directory"
    
    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$SCRIPT_DIR"
    
    print_status "Project directory: $PROJECT_DIR"
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_DIR/manage.py" ]]; then
        print_error "manage.py not found in current directory!"
        print_error "Please run this script from the olgFeast project root."
        exit 1
    fi
    
    print_status "Project directory verified ✓"
}

# Function to create virtual environment
create_virtual_environment() {
    print_header "🐍 Setting Up Python Virtual Environment"
    
    cd "$PROJECT_DIR"
    
    # Remove existing virtual environment if it exists
    if [[ -d "venv_omarchy" ]]; then
        print_warning "Removing existing virtual environment..."
        rm -rf venv_omarchy
    fi
    
    print_status "Creating virtual environment..."
    python -m venv venv_omarchy
    
    print_status "Activating virtual environment..."
    source venv_omarchy/bin/activate
    
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_status "Virtual environment created successfully ✓"
}

# Function to install Python dependencies
install_dependencies() {
    print_header "📚 Installing Python Dependencies"
    
    cd "$PROJECT_DIR"
    source venv_omarchy/bin/activate
    
    print_status "Installing requirements from requirements.txt..."
    pip install -r requirements.txt
    
    # Install additional production dependencies
    print_status "Installing additional production dependencies..."
    pip install gunicorn psycopg2-binary
    
    print_status "All dependencies installed successfully ✓"
}

# Function to configure Django
configure_django() {
    print_header "⚙️  Configuring Django Application"
    
    cd "$PROJECT_DIR"
    source venv_omarchy/bin/activate
    
    print_status "Running Django system check..."
    python manage.py check
    
    print_status "Creating database migrations..."
    python manage.py makemigrations
    
    print_status "Applying database migrations..."
    python manage.py migrate
    
    print_status "Collecting static files..."
    python manage.py collectstatic --noinput
    
    print_status "Django configured successfully ✓"
}

# Function to create superuser
create_superuser() {
    print_header "👤 Creating Admin User"
    
    cd "$PROJECT_DIR"
    source venv_omarchy/bin/activate
    
    print_warning "You'll need to create an admin user."
    print_warning "Press Enter to continue and create a superuser, or Ctrl+C to skip..."
    read -r
    
    python manage.py createsuperuser
    
    print_status "Admin user created successfully ✓"
}

# Function to configure Nginx
configure_nginx() {
    print_header "🌐 Configuring Nginx"
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/olgfeast > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
    }
    
    location /media/ {
        alias $PROJECT_DIR/media/;
    }
}
EOF
    
    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/olgfeast /etc/nginx/sites-enabled/
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    sudo nginx -t
    
    # Reload Nginx
    sudo systemctl reload nginx
    
    print_status "Nginx configured successfully ✓"
}

# Function to create systemd service
create_systemd_service() {
    print_header "🔧 Creating System Service"
    
    # Get current user
    CURRENT_USER=$(whoami)
    
    # Create systemd service file
    sudo tee /etc/systemd/system/olgfeast.service > /dev/null <<EOF
[Unit]
Description=olgFeast Django Application
After=network.target redis.service

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv_omarchy/bin
ExecStart=$PROJECT_DIR/venv_omarchy/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 olgFeast.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable olgfeast
    
    print_status "System service created successfully ✓"
}

# Function to start the application
start_application() {
    print_header "🚀 Starting olgFeast Application"
    
    print_status "Starting olgFeast service..."
    sudo systemctl start olgfeast
    
    # Wait a moment for the service to start
    sleep 3
    
    # Check if service is running
    if sudo systemctl is-active --quiet olgfeast; then
        print_status "olgFeast service started successfully ✓"
    else
        print_error "Failed to start olgFeast service!"
        print_status "Checking service status..."
        sudo systemctl status olgfeast
        exit 1
    fi
}

# Function to run tests
run_tests() {
    print_header "🧪 Running Test Suite"
    
    cd "$PROJECT_DIR"
    source venv_omarchy/bin/activate
    
    print_status "Running Django tests..."
    python manage.py test --verbosity=2
    
    print_status "All tests completed ✓"
}

# Function to display final information
display_final_info() {
    print_header "🎉 Installation Complete!"
    
    echo -e "${GREEN}olgFeast has been successfully installed and configured!${NC}"
    echo ""
    echo -e "${CYAN}Access your application at:${NC}"
    echo -e "  🌐 Web Interface: ${BLUE}http://localhost${NC}"
    echo -e "  🔧 Admin Panel: ${BLUE}http://localhost/admin${NC}"
    echo -e "  📊 Order Tracking: ${BLUE}http://localhost/operations/orders${NC}"
    echo ""
    echo -e "${CYAN}Service Management:${NC}"
    echo -e "  ▶️  Start: ${BLUE}sudo systemctl start olgfeast${NC}"
    echo -e "  ⏹️  Stop: ${BLUE}sudo systemctl stop olgfeast${NC}"
    echo -e "  🔄 Restart: ${BLUE}sudo systemctl restart olgfeast${NC}"
    echo -e "  📊 Status: ${BLUE}sudo systemctl status olgfeast${NC}"
    echo ""
    echo -e "${CYAN}Logs:${NC}"
    echo -e "  📝 Application logs: ${BLUE}sudo journalctl -u olgfeast -f${NC}"
    echo -e "  🌐 Nginx logs: ${BLUE}sudo tail -f /var/log/nginx/access.log${NC}"
    echo ""
    echo -e "${YELLOW}Note: Redis is running for WebSocket functionality${NC}"
    echo -e "${YELLOW}Note: Nginx is configured as a reverse proxy${NC}"
    echo ""
    echo -e "${GREEN}Enjoy your olgFeast restaurant management system! 🍽️${NC}"
}

# Function to handle cleanup on exit
cleanup() {
    print_warning "Installation interrupted. Cleaning up..."
    # Add any cleanup code here if needed
    exit 1
}

# Main installation function
main() {
    print_header "🍽️ olgFeast - Omarchy Installation Script"
    echo -e "${CYAN}This script will install and configure olgFeast on your Omarchy system.${NC}"
    echo -e "${CYAN}The installation includes:${NC}"
    echo -e "  • System package updates"
    echo -e "  • Python environment setup"
    echo -e "  • Django application configuration"
    echo -e "  • Redis for WebSocket functionality"
    echo -e "  • Nginx reverse proxy"
    echo -e "  • Systemd service configuration"
    echo ""
    echo -e "${YELLOW}This process may take several minutes.${NC}"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    
    # Set trap for cleanup
    trap cleanup INT TERM
    
    # Run installation steps
    check_root
    check_arch
    update_system
    install_packages
    setup_services
    setup_project_directory
    create_virtual_environment
    install_dependencies
    configure_django
    create_superuser
    configure_nginx
    create_systemd_service
    start_application
    run_tests
    display_final_info
}

# Run main function
main "$@"
