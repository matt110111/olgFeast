# 🚀 olgFeast Installation Guide

## Quick Installation (Recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/matt110111/olgFeast.git
cd olgFeast
```

### 2. Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Requirements (Choose one method)

#### Method A: Full Installation
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Method B: Minimal Installation (if full fails)
```bash
pip install --upgrade pip
pip install -r requirements-minimal.txt
```

#### Method C: Manual Installation (if both fail)
```bash
pip install --upgrade pip
pip install Django==5.2.6
pip install django-crispy-forms==2.3
pip install crispy-bootstrap3==2024.1
pip install django-allauth==0.66.0
pip install Pillow==11.0.0
pip install requests==2.32.3
pip install stripe==14.15.0
```

### 4. Setup Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Run the Server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000** 🎉

---

## Troubleshooting

### If you get "No module named 'django'" error:
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Verify Django is installed
pip list | grep Django
```

### If package versions don't exist:
```bash
# Try without version pins
pip install Django
pip install django-crispy-forms
pip install crispy-bootstrap3
pip install django-allauth
pip install Pillow
pip install requests
pip install stripe
```

### If you get permission errors on Linux/macOS:
```bash
sudo chmod +x *.sh
sudo chmod +x *.py
```

### If port 8000 is already in use:
```bash
python manage.py runserver 8080
```

---

## Alternative Installation Methods

### Using pip-tools (if available)
```bash
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt
```

### Using conda
```bash
conda create -n olgfeast python=3.11
conda activate olgfeast
pip install -r requirements.txt
```

---

## Verification

After installation, run these commands to verify everything works:

```bash
# Check Django installation
python manage.py check

# Run tests
python quick_test.py

# Start server
python manage.py runserver
```

---

## Support

If you continue to have issues:

1. **Check Python version**: `python --version` (should be 3.8+)
2. **Check pip version**: `pip --version`
3. **Update pip**: `pip install --upgrade pip`
4. **Clear pip cache**: `pip cache purge`
5. **Try fresh virtual environment**: Delete `venv` folder and recreate

For additional help, check the main README.md or create an issue on GitHub.
