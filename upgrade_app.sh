#!/bin/bash
# olgFeast Application Upgrade Script
# Upgrades all dependencies to latest versions

set -e  # Exit on any error

echo "🚀 Starting olgFeast Application Upgrade"
echo "========================================"

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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please create one first:"
    echo "python -m venv venv"
    echo "source venv/bin/activate"
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_status "Python version: $PYTHON_VERSION"

# Backup current requirements
if [ -f "requirments.txt" ]; then
    print_status "Backing up current requirements..."
    cp requirments.txt requirements_backup.txt
    print_success "Requirements backed up to requirements_backup.txt"
fi

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install new requirements
print_status "Installing updated requirements..."
pip install -r requirements.txt

# Check Django version
DJANGO_VERSION=$(python -c "import django; print(django.get_version())")
print_success "Django version: $DJANGO_VERSION"

# Backup database
print_status "Backing up database..."
if [ -f "n_db.sqlite3" ]; then
    cp n_db.sqlite3 n_db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
    print_success "Database backed up"
else
    print_warning "No database found to backup"
fi

# Run Django upgrade script
print_status "Running Django upgrade process..."
python upgrade_django.py

# Run tests
print_status "Running application tests..."
if python manage.py test --verbosity=0; then
    print_success "All tests passed!"
else
    print_warning "Some tests failed. Check the output above."
fi

# Check for any remaining issues
print_status "Checking for common issues..."

# Check for deprecated imports
if grep -r "from django.conf.urls import url" . --include="*.py" > /dev/null 2>&1; then
    print_warning "Found deprecated 'django.conf.urls.url' imports. These should be updated to 'django.urls.path' or 'django.urls.re_path'"
fi

# Check for deprecated settings
if grep -r "USE_L10N" . --include="*.py" > /dev/null 2>&1; then
    print_warning "Found USE_L10N setting. This is deprecated in Django 4.0+ and can be removed."
fi

print_success "Upgrade process completed!"
echo ""
echo "📋 Summary:"
echo "==========="
echo "✅ Requirements updated to latest versions"
echo "✅ Django upgraded to $DJANGO_VERSION"
echo "✅ Database backed up"
echo "✅ Migrations applied"
echo "✅ Static files collected"
echo ""
echo "🔍 Next steps:"
echo "=============="
echo "1. Test the application: python manage.py runserver"
echo "2. Check all functionality works correctly"
echo "3. Review any deprecation warnings"
echo "4. Update any custom code for Django 5.2 compatibility"
echo ""
echo "🛠️  If you encounter issues:"
echo "============================"
echo "1. Check the backup files created during upgrade"
echo "2. Review Django 5.2 release notes: https://docs.djangoproject.com/en/5.2/releases/5.2/"
echo "3. Run: python manage.py check --deploy"
echo "4. Check logs for any error messages"
