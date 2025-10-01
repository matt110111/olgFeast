# 🚀 One-Command Installation

## Super Quick Start

### Clone and Install (One Command)
```bash
git clone https://github.com/matt110111/olgFeast.git && cd olgFeast && ./install
```

### Or Choose Your Platform

#### 🐧 Linux/macOS
```bash
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast
./install.sh
```

#### 🪟 Windows
```cmd
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast
install.bat
```

#### 🐍 Cross-Platform (Python)
```bash
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast
python install.py
```

---

## What the Installer Does

The one-command installer automatically:

✅ **Checks Python installation** (requires Python 3.8+)  
✅ **Creates virtual environment** (`venv/`)  
✅ **Installs all dependencies** (with fallback options)  
✅ **Sets up Django database** (migrations, etc.)  
✅ **Creates admin superuser** (admin/admin123)  
✅ **Collects static files**  
✅ **Creates startup scripts**  
✅ **Tests the installation**  

---

## After Installation

### Start the Server
```bash
# Linux/macOS
./start_server.sh

# Windows
start_server.bat

# Or manually
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
python manage.py runserver
```

### Access the Application
- **Website**: http://127.0.0.1:8000
- **Admin Panel**: http://127.0.0.1:8000/admin
- **Username**: admin
- **Password**: admin123

---

## Troubleshooting

### If Installation Fails

#### Try Manual Installation
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows
pip install --upgrade pip
pip install -r requirements-minimal.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

#### Check Python Version
```bash
python --version  # Should be 3.8+
```

#### Check pip
```bash
pip --version
pip install --upgrade pip
```

#### Clear pip Cache
```bash
pip cache purge
```

---

## Installation Options

The installer tries multiple approaches:

1. **Minimal Installation** (`requirements-minimal.txt`) - Essential packages only
2. **Flexible Installation** (`requirements-flexible.txt`) - Version ranges
3. **Full Installation** (`requirements.txt`) - Exact versions
4. **Manual Installation** - Individual package installation

---

## Features Included

- ✅ Django 5.2.6 (Latest LTS)
- ✅ Shopping cart functionality
- ✅ Live order tracking
- ✅ User authentication
- ✅ Admin interface
- ✅ Payment processing (Stripe/Braintree)
- ✅ Image handling (Pillow)
- ✅ Modern UI (Bootstrap 3)

---

## Support

If you encounter issues:

1. **Check the logs** - The installer shows detailed output
2. **Try different methods** - Multiple installation approaches available
3. **Check requirements** - Ensure Python 3.8+ and pip are installed
4. **See INSTALLATION_GUIDE.md** - Detailed troubleshooting guide
5. **Create an issue** - On GitHub for additional help

---

## Quick Commands Reference

```bash
# Install
./install                    # Universal installer
./install.sh                 # Linux/macOS
install.bat                  # Windows
python install.py           # Cross-platform

# Start
./start_server.sh           # Linux/macOS
start_server.bat            # Windows
python manage.py runserver  # Manual

# Test
python quick_test.py        # Quick functionality test
python test_add_to_cart.py  # Detailed cart test
```

---

**🎉 That's it! Your olgFeast restaurant management system is ready to use!**
