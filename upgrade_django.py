#!/usr/bin/env python
"""
Django Upgrade Script for olgFeast
Upgrades from Django 2.2.2 to Django 5.2.6
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
    django.setup()

def backup_database():
    """Create backup of current database"""
    import shutil
    db_path = 'n_db.sqlite3'
    backup_path = 'n_db.sqlite3.backup'
    
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database backed up to {backup_path}")
    else:
        print("⚠️  No database found to backup")

def run_migrations():
    """Run Django migrations"""
    print("🔄 Running migrations...")
    
    try:
        # Make migrations for all apps
        execute_from_command_line(['manage.py', 'makemigrations'])
        print("✅ Made migrations")
        
        # Apply migrations
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Applied migrations")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    
    return True

def collect_static():
    """Collect static files"""
    print("🔄 Collecting static files...")
    
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected")
    except Exception as e:
        print(f"❌ Static files collection error: {e}")
        return False
    
    return True

def check_django_version():
    """Check current Django version"""
    print(f"🐍 Python version: {sys.version}")
    print(f"📦 Django version: {django.get_version()}")

def main():
    """Main upgrade process"""
    print("🚀 Starting Django upgrade process...")
    print("=" * 50)
    
    # Check versions
    check_django_version()
    print()
    
    # Backup database
    backup_database()
    print()
    
    # Setup Django
    setup_django()
    print()
    
    # Run migrations
    if not run_migrations():
        print("❌ Upgrade failed at migrations")
        return False
    
    print()
    
    # Collect static files
    if not collect_static():
        print("❌ Upgrade failed at static files")
        return False
    
    print()
    print("✅ Django upgrade completed successfully!")
    print("=" * 50)
    print("📋 Next steps:")
    print("1. Test the application: python manage.py runserver")
    print("2. Run tests: python manage.py test")
    print("3. Check admin interface")
    print("4. Verify all functionality works")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
