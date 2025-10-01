#!/bin/bash
# Quick fix for Arch Linux installation
# Run this from your current olgFeast directory

echo "🔧 Fixing Arch Linux Installation"
echo "================================="
echo ""

# Remove existing virtual environment if it has issues
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create fresh virtual environment
echo "📦 Creating fresh virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install essential packages
echo "📥 Installing essential packages..."
pip install Django==5.2.6
pip install django-crispy-forms==2.3
pip install crispy-bootstrap3==2024.1
pip install django-allauth==0.66.0
pip install Pillow==11.0.0
pip install requests==2.32.3
pip install stripe==14.15.0

# Run migrations
echo "🗄️  Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if needed
echo "👤 Checking superuser..."
if ! python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(is_superuser=True).exists()" 2>/dev/null; then
    echo "Creating superuser..."
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell
fi

# Create startup script
echo "📝 Creating startup script..."
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

echo ""
echo "✅ Fix complete!"
echo "================="
echo ""
echo "🚀 To start the server:"
echo "   ./start_server.sh"
echo ""
echo "🌐 Then visit: http://127.0.0.1:8000"
echo "👤 Admin: admin/admin123"
echo ""
