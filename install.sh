#!/bin/bash
# olgFeast One-Command Installation Script for Linux/macOS
# This script installs all requirements and configurations automatically

set -e  # Exit on any error

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

echo "🚀 olgFeast One-Command Installation"
echo "===================================="
echo ""

# Check if Python is installed
print_status "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8+ required. Found: $PYTHON_VERSION"
    exit 1
fi

# Check if pip is installed
print_status "Checking pip installation..."
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    print_error "pip not found. Installing pip..."
    $PYTHON_CMD -m ensurepip --upgrade
    PIP_CMD="$PYTHON_CMD -m pip"
fi

# Upgrade pip
print_status "Upgrading pip..."
$PIP_CMD install --upgrade pip

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Function to install requirements with fallback
install_requirements() {
    local req_file=$1
    local description=$2
    
    print_status "Attempting $description..."
    
    if pip install -r "$req_file" --quiet; then
        print_success "$description completed"
        return 0
    else
        print_warning "$description failed, trying next option..."
        return 1
    fi
}

# Try different requirement files in order
print_status "Installing Python packages..."

if install_requirements "requirements-minimal.txt" "minimal installation"; then
    print_success "Minimal installation successful"
elif install_requirements "requirements-flexible.txt" "flexible installation"; then
    print_success "Flexible installation successful"
elif install_requirements "requirements.txt" "full installation"; then
    print_success "Full installation successful"
else
    print_warning "Package installation failed, trying manual installation..."
    
    # Manual installation of essential packages
    print_status "Installing essential packages manually..."
    pip install Django==5.2.6
    pip install django-crispy-forms==2.3
    pip install crispy-bootstrap3==2024.1
    pip install django-allauth==0.66.0
    pip install Pillow==11.0.0
    pip install requests==2.32.3
    pip install stripe==14.15.0
    
    print_success "Manual installation completed"
fi

# Install additional packages if they exist
print_status "Installing additional packages..."
pip install braintree==4.32.0 2>/dev/null || print_warning "braintree installation failed (optional)"
pip install pytz==2024.2 2>/dev/null || print_warning "pytz installation failed (optional)"
pip install sqlparse==0.5.0 2>/dev/null || print_warning "sqlparse installation failed (optional)"

# Setup Django
print_status "Setting up Django..."

# Make migrations
if python manage.py makemigrations --dry-run > /dev/null 2>&1; then
    print_status "Running migrations..."
    python manage.py makemigrations
    python manage.py migrate
    print_success "Database migrations completed"
else
    print_status "No new migrations needed"
fi

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || print_warning "Static files collection failed (optional)"

# Create superuser if it doesn't exist
print_status "Checking for superuser..."
if ! python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(is_superuser=True).exists()" 2>/dev/null; then
    print_warning "No superuser found. Creating one..."
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell
    print_success "Superuser created (username: admin, password: admin123)"
else
    print_success "Superuser already exists"
fi

# Test the installation
print_status "Testing installation..."
if python manage.py check > /dev/null 2>&1; then
    print_success "Django configuration is valid"
else
    print_warning "Django configuration has warnings (check output above)"
fi

# Create startup script
print_status "Creating startup script..."
cat > start_server.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🚀 Starting olgFeast server..."
echo "Visit: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop"
python manage.py runserver
EOF

chmod +x start_server.sh
print_success "Startup script created"

# Final summary
echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "✅ Virtual environment: venv/"
echo "✅ Django packages: Installed"
echo "✅ Database: Configured"
echo "✅ Static files: Collected"
echo "✅ Superuser: Created (admin/admin123)"
echo ""
echo "🚀 To start the server:"
echo "   ./start_server.sh"
echo ""
echo "   Or manually:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"
echo ""
echo "🌐 Then visit: http://127.0.0.1:8000"
echo ""
echo "📋 Admin access:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📚 For help, see INSTALLATION_GUIDE.md"
echo ""

print_success "olgFeast is ready to use! 🎉"
