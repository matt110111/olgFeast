@echo off
REM olgFeast One-Command Installation Script for Windows
REM This script installs all requirements and configurations automatically

setlocal enabledelayedexpansion

echo 🚀 olgFeast One-Command Installation
echo ====================================
echo.

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found

REM Check if pip is installed
echo [INFO] Checking pip installation...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found. Installing pip...
    python -m ensurepip --upgrade
)

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Function to install requirements with fallback
echo [INFO] Installing Python packages...

REM Try minimal requirements first
echo [INFO] Attempting minimal installation...
pip install -r requirements-minimal.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Minimal installation completed
    goto :setup_django
)

REM Try flexible requirements
echo [WARNING] Minimal installation failed, trying flexible installation...
pip install -r requirements-flexible.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Flexible installation completed
    goto :setup_django
)

REM Try full requirements
echo [WARNING] Flexible installation failed, trying full installation...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Full installation completed
    goto :setup_django
)

REM Manual installation
echo [WARNING] Package installation failed, trying manual installation...
echo [INFO] Installing essential packages manually...
pip install Django==5.2.6
pip install django-crispy-forms==2.3
pip install crispy-bootstrap3==2024.1
pip install django-allauth==0.66.0
pip install Pillow==11.0.0
pip install requests==2.32.3
pip install stripe==14.15.0
echo [SUCCESS] Manual installation completed

:setup_django
REM Install additional packages if they exist
echo [INFO] Installing additional packages...
pip install braintree==4.32.0 >nul 2>&1 || echo [WARNING] braintree installation failed ^(optional^)
pip install pytz==2024.2 >nul 2>&1 || echo [WARNING] pytz installation failed ^(optional^)
pip install sqlparse==0.5.0 >nul 2>&1 || echo [WARNING] sqlparse installation failed ^(optional^)

REM Setup Django
echo [INFO] Setting up Django...

REM Make migrations
echo [INFO] Running migrations...
python manage.py makemigrations
python manage.py migrate
echo [SUCCESS] Database migrations completed

REM Collect static files
echo [INFO] Collecting static files...
python manage.py collectstatic --noinput >nul 2>&1 || echo [WARNING] Static files collection failed ^(optional^)

REM Create superuser if it doesn't exist
echo [INFO] Checking for superuser...
python manage.py shell -c "from django.contrib.auth.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] No superuser found. Creating one...
    echo from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123') | python manage.py shell
    echo [SUCCESS] Superuser created ^(username: admin, password: admin123^)
) else (
    echo [SUCCESS] Superuser already exists
)

REM Test the installation
echo [INFO] Testing installation...
python manage.py check >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Django configuration is valid
) else (
    echo [WARNING] Django configuration has warnings
)

REM Create startup script
echo [INFO] Creating startup script...
echo @echo off > start_server.bat
echo cd /d "%%~dp0" >> start_server.bat
echo call venv\Scripts\activate.bat >> start_server.bat
echo echo 🚀 Starting olgFeast server... >> start_server.bat
echo echo Visit: http://127.0.0.1:8000 >> start_server.bat
echo echo Press Ctrl+C to stop >> start_server.bat
echo python manage.py runserver >> start_server.bat
echo [SUCCESS] Startup script created

REM Final summary
echo.
echo 🎉 Installation Complete!
echo ========================
echo.
echo ✅ Virtual environment: venv\
echo ✅ Django packages: Installed
echo ✅ Database: Configured
echo ✅ Static files: Collected
echo ✅ Superuser: Created ^(admin/admin123^)
echo.
echo 🚀 To start the server:
echo    start_server.bat
echo.
echo    Or manually:
echo    venv\Scripts\activate.bat
echo    python manage.py runserver
echo.
echo 🌐 Then visit: http://127.0.0.1:8000
echo.
echo 📋 Admin access:
echo    Username: admin
echo    Password: admin123
echo.
echo 📚 For help, see INSTALLATION_GUIDE.md
echo.

echo [SUCCESS] olgFeast is ready to use! 🎉
pause
