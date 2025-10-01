# 🍽️ olgFeast - Restaurant Order Management System

A modern Django-based restaurant order management system with live order tracking, shopping cart functionality, and staff management tools.

## ✨ Features

- **🛒 Shopping Cart**: Add items, modify quantities, and manage orders
- **📱 Live Order Tracking**: Real-time order status updates with horizontal workflow
- **👥 User Management**: Customer registration and staff authentication
- **🎯 Clickable Order Cards**: Easy order status management for staff
- **📊 Order Analytics**: Track orders through Pending → Preparing → Ready → Complete
- **🧪 Comprehensive Testing**: Full test suite for reliable deployment
- **🔧 Admin Tools**: Staff-only order management controls

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (3.13 recommended)
- **Git** for cloning the repository
- **Virtual Environment** (recommended)

### 🔄 Upgrading from Older Versions

If you're upgrading from an older version of olgFeast:

```bash
# Run the automated upgrade script
./upgrade_app.sh

# Or manually upgrade
pip install -r requirements.txt
python upgrade_django.py
```

**Note**: The application now uses Django 5.2.6 with the latest package versions.

### 📋 Installation Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast
```

#### 2. Set Up Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set Up Database
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

#### 6. Run the Server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000** 🎉

---

## 🖥️ Platform-Specific Setup

### 🐧 Linux Setup (Ubuntu/Debian)

```bash
# Update package manager
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git

# Clone and setup project
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Run server
python manage.py runserver
```

### 🍎 macOS Setup

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python git

# Clone and setup project
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Run server
python manage.py runserver
```

### 🪟 Windows Setup

#### Using Command Prompt:
```cmd
# Install Python from https://python.org (check "Add to PATH")

# Clone repository (install Git from https://git-scm.com if needed)
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Run server
python manage.py runserver
```

#### Using PowerShell:
```powershell
# Same commands as above, but use:
venv\Scripts\Activate.ps1
# instead of:
venv\Scripts\activate
```

---

## 👤 First Steps After Installation

### 1. Register Your First User
1. Visit: **http://127.0.0.1:8000/register/**
2. Create an account with your details
3. You'll be automatically logged in

### 2. Create Staff User (Optional)
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.create_user('staff', 'staff@example.com', 'password123')
user.is_staff = True
user.save()
exit()
```

### 3. Browse Menu & Place Orders
1. Visit: **http://127.0.0.1:8000/shop/**
2. Browse available food items
3. Add items to your cart
4. View cart: **http://127.0.0.1:8000/cart/order-summary/**
5. Checkout when ready

### 4. Track Orders (Staff Only)
1. Login as staff user
2. Visit: **http://127.0.0.1:8000/cart/order-tracking/**
3. Click on orders to update status:
   - **Pending** → **Preparing** → **Ready** → **Complete**

---

## 🧪 Testing

### Quick Functionality Test
```bash
python quick_test.py
```

### Full Test Suite
```bash
./run_all_tests.sh
```

### Individual App Tests
```bash
python manage.py test shopping_cart
python manage.py test accounts
python manage.py test shop_front
```

---

## 🗄️ Database Management

### Clear All Data (Fresh Start)
```bash
python clear_transactions.py
```
⚠️ **Warning**: This removes all users, profiles, and transactions!

### Reset Database (Nuclear Option)
```bash
rm n_db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file for custom settings:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///n_db.sqlite3
```

### Django Settings
Key settings in `olgFeast/settings.py`:
- `DEBUG = True` (for development)
- `ALLOWED_HOSTS = ['*']` (for testing)
- `CRISPY_TEMPLATE_PACK = 'bootstrap3'`
- `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'` (Django 5.2+)

### Requirements Files
- `requirements.txt` - Base requirements for all environments
- `requirements-dev.txt` - Development tools and testing
- `requirements-prod.txt` - Production deployment with additional security and performance packages

---

## 📁 Project Structure

```
olgFeast/
├── accounts/              # User profiles and authentication
├── shop_front/           # Menu display and item management
├── shopping_cart/        # Cart functionality and order tracking
├── users/                # User registration and login
├── olgFeast/            # Main Django settings
├── templates/           # Base templates
├── static/              # CSS, JS, and static files
├── n_db.sqlite3         # SQLite database
├── requirements.txt     # Python dependencies
├── manage.py           # Django management script
└── README.md           # This file
```

---

## 🌐 URLs and Navigation

| URL | Description | Access |
|-----|-------------|--------|
| `/` | Home page | Public |
| `/shop/` | Browse menu | Authenticated |
| `/cart/order-summary/` | View cart | Authenticated |
| `/cart/order-tracking/` | Live order tracking | Staff only |
| `/register/` | User registration | Public |
| `/login/` | User login | Public |
| `/logout/` | User logout | Authenticated |
| `/admin/` | Django admin | Superuser only |

---

## 🚨 Troubleshooting

### Common Issues

#### 1. **ModuleNotFoundError: No module named 'django'**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install Django
pip install Django==5.2.6
```

#### 2. **Database is locked**
```bash
# Stop any running Django servers
# Delete database and recreate
rm n_db.sqlite3
python manage.py migrate
```

#### 3. **Permission denied on Linux/macOS**
```bash
# Make scripts executable
chmod +x run_all_tests.sh
chmod +x clear_transactions.py
```

#### 4. **Port 8000 already in use**
```bash
# Use different port
python manage.py runserver 8080
```

#### 5. **Git push authentication failed**
```bash
# Set up SSH keys or use HTTPS with token
git remote set-url origin https://github.com/username/olgFeast.git
```

### Getting Help

1. **Check the test suite**: `python quick_test.py`
2. **Review Django logs**: Check terminal output for errors
3. **Verify database**: `python manage.py shell` then `from django.db import connection; connection.cursor()`
4. **Check dependencies**: `pip list | grep Django`

---

## 🔄 Development Workflow

### Making Changes
1. **Run tests first**: `python quick_test.py`
2. **Make your changes**
3. **Run tests again**: `python quick_test.py`
4. **Commit changes**: `git add . && git commit -m "Your message"`
5. **Push to repository**: `git push origin master`

### Adding New Features
1. Create new Django app: `python manage.py startapp new_feature`
2. Add to `INSTALLED_APPS` in settings.py
3. Create models, views, and templates
4. Add tests to `new_feature/tests.py`
5. Update documentation

---

## 📊 System Requirements

### Minimum Requirements
- **Python**: 3.8+
- **RAM**: 512MB
- **Storage**: 100MB
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+

### Recommended
- **Python**: 3.13
- **RAM**: 2GB+
- **Storage**: 1GB+
- **OS**: Latest version of your platform

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `python quick_test.py`
5. Commit changes: `git commit -m "Add feature-name"`
6. Push to branch: `git push origin feature-name`
7. Create a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🎯 Roadmap

- [ ] Payment integration (Stripe/PayPal)
- [ ] Email notifications
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Multi-location support
- [ ] Inventory management
- [ ] Customer loyalty program

---

**Happy Coding! 🚀**

For support, create an issue on GitHub or contact the development team.