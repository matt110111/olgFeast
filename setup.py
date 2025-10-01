#!/usr/bin/env python3
"""
olgFeast Quick Setup Script
Automated setup for fresh installations
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def setup_olgfeast():
    """Main setup function"""
    print("🚀 olgFeast Quick Setup")
    print("=" * 30)
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print("❌ Python 3.8+ required. Current version:", f"{python_version.major}.{python_version.minor}")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    
    # Determine OS
    os_name = platform.system().lower()
    print(f"🖥️  Operating System: {os_name}")
    
    # Setup virtual environment
    if os.path.exists('venv'):
        print("ℹ️  Virtual environment already exists")
    else:
        if not run_command('python -m venv venv', 'Creating virtual environment'):
            return False
    
    # Activate virtual environment and install dependencies
    if os_name == 'windows':
        pip_cmd = 'venv\\Scripts\\pip'
        python_cmd = 'venv\\Scripts\\python'
    else:
        pip_cmd = 'venv/bin/pip'
        python_cmd = 'venv/bin/python'
    
    # Install dependencies
    if not run_command(f'{pip_cmd} install -r requirements.txt', 'Installing dependencies'):
        return False
    
    # Run Django migrations
    if not run_command(f'{python_cmd} manage.py makemigrations', 'Creating database migrations'):
        return False
    
    if not run_command(f'{python_cmd} manage.py migrate', 'Applying database migrations'):
        return False
    
    # Run tests to verify setup
    print("\n🧪 Running functionality tests...")
    if not run_command(f'{python_cmd} quick_test.py', 'Testing installation'):
        print("⚠️  Tests failed, but installation may still work")
    
    print("\n🎉 Setup Complete!")
    print("=" * 30)
    print("Next steps:")
    print("1. Activate virtual environment:")
    if os_name == 'windows':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Start the server:")
    print("   python manage.py runserver")
    print("3. Visit: http://127.0.0.1:8000")
    print("\nFor detailed instructions, see README.md")
    
    return True

if __name__ == "__main__":
    success = setup_olgfeast()
    sys.exit(0 if success else 1)
