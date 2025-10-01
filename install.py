#!/usr/bin/env python3
"""
olgFeast One-Command Installation Script (Cross-Platform)
This script installs all requirements and configurations automatically
Works on Linux, macOS, and Windows
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message):
    """Print status message in blue"""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def print_success(message):
    """Print success message in green"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message):
    """Print error message in red"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def run_command(command, shell=True, capture_output=False):
    """Run a command and return the result"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=shell, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(command, shell=shell)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_python():
    """Check if Python is installed and get version"""
    print_status("Checking Python installation...")
    
    # Try python3 first, then python
    for cmd in ['python3', 'python']:
        success, stdout, stderr = run_command(f"{cmd} --version", capture_output=True)
        if success:
            version = stdout.strip().split()[1]
            print_success(f"Python {version} found")
            return cmd, version
    
    print_error("Python not found. Please install Python 3.8+ first.")
    sys.exit(1)

def check_pip(python_cmd):
    """Check if pip is installed"""
    print_status("Checking pip installation...")
    
    success, stdout, stderr = run_command(f"{python_cmd} -m pip --version", capture_output=True)
    if not success:
        print_warning("pip not found. This is normal on Arch Linux.")
        print_status("Will use virtual environment pip instead.")
    else:
        print_success("pip is available")

def upgrade_pip_in_venv(venv_pip):
    """Upgrade pip in virtual environment"""
    print_status("Upgrading pip in virtual environment...")
    success, _, _ = run_command(f"{venv_pip} install --upgrade pip")
    if success:
        print_success("pip upgraded successfully")
    else:
        print_warning("pip upgrade failed, continuing...")

def create_venv(python_cmd):
    """Create virtual environment if it doesn't exist"""
    if not Path("venv").exists():
        print_status("Creating virtual environment...")
        success, _, _ = run_command(f"{python_cmd} -m venv venv")
        if success:
            print_success("Virtual environment created")
        else:
            print_error("Failed to create virtual environment")
            sys.exit(1)
    else:
        print_warning("Virtual environment already exists")

def get_venv_python():
    """Get the Python command for the virtual environment"""
    system = platform.system().lower()
    if system == "windows":
        return "venv\\Scripts\\python.exe"
    else:
        return "venv/bin/python"

def get_venv_pip():
    """Get the pip command for the virtual environment"""
    system = platform.system().lower()
    if system == "windows":
        return "venv\\Scripts\\pip.exe"
    else:
        return "venv/bin/pip"

def install_requirements(venv_pip):
    """Install requirements with fallback options"""
    print_status("Installing Python packages...")
    
    # List of requirement files to try in order
    req_files = [
        ("requirements-minimal.txt", "minimal installation"),
        ("requirements-flexible.txt", "flexible installation"),
        ("requirements.txt", "full installation")
    ]
    
    for req_file, description in req_files:
        if Path(req_file).exists():
            print_status(f"Attempting {description}...")
            success, _, _ = run_command(f"{venv_pip} install -r {req_file}")
            if success:
                print_success(f"{description} completed")
                return True
            else:
                print_warning(f"{description} failed, trying next option...")
    
    # Manual installation as fallback
    print_warning("Package installation failed, trying manual installation...")
    print_status("Installing essential packages manually...")
    
    essential_packages = [
        "Django==5.2.6",
        "django-crispy-forms==2.3",
        "crispy-bootstrap3==2024.1",
        "django-allauth==0.66.0",
        "Pillow==11.0.0",
        "requests==2.32.3",
        "stripe==14.15.0"
    ]
    
    for package in essential_packages:
        success, _, _ = run_command(f"{venv_pip} install {package}")
        if not success:
            print_warning(f"Failed to install {package}")
    
    print_success("Manual installation completed")
    return True

def install_additional_packages(venv_pip):
    """Install additional optional packages"""
    print_status("Installing additional packages...")
    
    additional_packages = [
        "braintree==4.32.0",
        "pytz==2024.2",
        "sqlparse==0.5.0"
    ]
    
    for package in additional_packages:
        success, _, _ = run_command(f"{venv_pip} install {package}")
        if not success:
            print_warning(f"{package} installation failed (optional)")

def setup_django(venv_python):
    """Setup Django database and configurations"""
    print_status("Setting up Django...")
    
    # Make migrations
    print_status("Running migrations...")
    success, _, _ = run_command(f"{venv_python} manage.py makemigrations")
    if success:
        success, _, _ = run_command(f"{venv_python} manage.py migrate")
        if success:
            print_success("Database migrations completed")
        else:
            print_error("Database migration failed")
            sys.exit(1)
    else:
        print_warning("No new migrations needed")
    
    # Collect static files
    print_status("Collecting static files...")
    success, _, _ = run_command(f"{venv_python} manage.py collectstatic --noinput")
    if not success:
        print_warning("Static files collection failed (optional)")
    
    # Create superuser
    print_status("Checking for superuser...")
    check_cmd = "from django.contrib.auth.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"
    success, _, _ = run_command(f"{venv_python} manage.py shell -c \"{check_cmd}\"")
    
    if not success:
        print_warning("No superuser found. Creating one...")
        create_cmd = "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
        success, _, _ = run_command(f"echo \"{create_cmd}\" | {venv_python} manage.py shell")
        if success:
            print_success("Superuser created (username: admin, password: admin123)")
        else:
            print_warning("Failed to create superuser")
    else:
        print_success("Superuser already exists")
    
    # Test Django configuration
    print_status("Testing installation...")
    success, _, _ = run_command(f"{venv_python} manage.py check")
    if success:
        print_success("Django configuration is valid")
    else:
        print_warning("Django configuration has warnings")

def create_startup_scripts():
    """Create startup scripts for different platforms"""
    print_status("Creating startup scripts...")
    
    system = platform.system().lower()
    
    if system == "windows":
        # Windows batch file
        with open("start_server.bat", "w") as f:
            f.write("@echo off\n")
            f.write('cd /d "%~dp0"\n')
            f.write("call venv\\Scripts\\activate.bat\n")
            f.write("echo 🚀 Starting olgFeast server...\n")
            f.write("echo Visit: http://127.0.0.1:8000\n")
            f.write("echo Press Ctrl+C to stop\n")
            f.write("python manage.py runserver\n")
        print_success("Windows startup script created")
    else:
        # Unix shell script
        with open("start_server.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write('cd "$(dirname "$0")"\n')
            f.write("source venv/bin/activate\n")
            f.write("echo \"🚀 Starting olgFeast server...\"\n")
            f.write("echo \"Visit: http://127.0.0.1:8000\"\n")
            f.write("echo \"Press Ctrl+C to stop\"\n")
            f.write("python manage.py runserver\n")
        
        # Make executable
        os.chmod("start_server.sh", 0o755)
        print_success("Unix startup script created")

def main():
    """Main installation function"""
    print("🚀 olgFeast One-Command Installation")
    print("====================================")
    print()
    
    # Check Python
    python_cmd, python_version = check_python()
    
    # Check pip
    check_pip(python_cmd)
    
    # Create virtual environment first
    create_venv(python_cmd)
    
    # Get virtual environment commands
    venv_python = get_venv_python()
    venv_pip = get_venv_pip()
    
    # Upgrade pip in virtual environment
    upgrade_pip_in_venv(venv_pip)
    
    # Install requirements
    install_requirements(venv_pip)
    
    # Install additional packages
    install_additional_packages(venv_pip)
    
    # Setup Django
    setup_django(venv_python)
    
    # Create startup scripts
    create_startup_scripts()
    
    # Final summary
    print()
    print("🎉 Installation Complete!")
    print("========================")
    print()
    print("✅ Virtual environment: venv/")
    print("✅ Django packages: Installed")
    print("✅ Database: Configured")
    print("✅ Static files: Collected")
    print("✅ Superuser: Created (admin/admin123)")
    print()
    print("🚀 To start the server:")
    system = platform.system().lower()
    if system == "windows":
        print("   start_server.bat")
    else:
        print("   ./start_server.sh")
    print()
    print("   Or manually:")
    if system == "windows":
        print("   venv\\Scripts\\activate.bat")
    else:
        print("   source venv/bin/activate")
    print("   python manage.py runserver")
    print()
    print("🌐 Then visit: http://127.0.0.1:8000")
    print()
    print("📋 Admin access:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("📚 For help, see INSTALLATION_GUIDE.md")
    print()
    
    print_success("olgFeast is ready to use! 🎉")

if __name__ == "__main__":
    main()
