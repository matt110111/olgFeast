#!/usr/bin/env python
"""
Test script to verify all requirements can be imported successfully
"""

import sys
import importlib

# List of packages to test
PACKAGES = [
    'django',
    'crispy_forms',
    'crispy_bootstrap3',
    'allauth',
    'PIL',  # Pillow
    'requests',
    'urllib3',
    'certifi',
    'lxml',
    'defusedxml',
    'cssselect',
    'pyquery',
    'markdown',
    'pygments',
    'oauthlib',
    'requests_oauthlib',
    'openid',
    'stripe',
    'braintree',
    'pytz',
    'django_tables2',
]

def test_imports():
    """Test importing all required packages"""
    print("🧪 Testing package imports...")
    print("=" * 50)
    
    failed_imports = []
    successful_imports = []
    
    for package in PACKAGES:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'Unknown')
            print(f"✅ {package}: {version}")
            successful_imports.append(package)
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed_imports.append(package)
        except Exception as e:
            print(f"⚠️  {package}: {e}")
            failed_imports.append(package)
    
    print("=" * 50)
    print(f"✅ Successful imports: {len(successful_imports)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    
    if failed_imports:
        print(f"\n❌ Failed packages: {', '.join(failed_imports)}")
        return False
    else:
        print("\n🎉 All packages imported successfully!")
        return True

def test_django_setup():
    """Test Django setup"""
    print("\n🐍 Testing Django setup...")
    print("=" * 50)
    
    try:
        import django
        from django.conf import settings
        from django.core.management import execute_from_command_line
        
        print(f"✅ Django version: {django.get_version()}")
        
        # Test Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
        django.setup()
        
        print("✅ Django setup successful")
        print(f"✅ DEBUG mode: {settings.DEBUG}")
        print(f"✅ Database: {settings.DATABASES['default']['ENGINE']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

if __name__ == '__main__':
    import os
    
    print("🚀 olgFeast Requirements Test")
    print("=" * 50)
    
    # Test package imports
    imports_ok = test_imports()
    
    # Test Django setup
    django_ok = test_django_setup()
    
    print("\n" + "=" * 50)
    if imports_ok and django_ok:
        print("🎉 All tests passed! Requirements are working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)
