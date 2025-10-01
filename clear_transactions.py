#!/usr/bin/env python3
"""
Clear All Transactions Script
Removes all transaction data to prepare for shipping clean code
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olgFeast.settings')
django.setup()

from shopping_cart.models import Transaction, Item
from accounts.models import Profile
from django.contrib.auth.models import User

def clear_all_transactions():
    """Clear all transactions and cart data"""
    print("🧹 Clearing all transaction data...")
    print("=" * 40)
    
    try:
        # Clear all transactions
        transaction_count = Transaction.objects.count()
        Transaction.objects.all().delete()
        print(f"✅ Deleted {transaction_count} transactions")
        
        # Clear all cart items
        total_items = 0
        for profile in Profile.objects.all():
            if hasattr(profile, 'inventory'):
                items_count = profile.inventory.item_set.count()
                profile.inventory.item_set.all().delete()
                total_items += items_count
        
        print(f"✅ Deleted {total_items} cart items")
        
        # Show remaining data
        remaining_transactions = Transaction.objects.count()
        remaining_items = Item.objects.count()
        
        print(f"\n📊 Remaining Data:")
        print(f"   Transactions: {remaining_transactions}")
        print(f"   Cart Items: {remaining_items}")
        print(f"   Users: {User.objects.count()}")
        print(f"   Profiles: {Profile.objects.count()}")
        print(f"   Food Items: {django.apps.apps.get_model('shop_front', 'FoodItem').objects.count()}")
        
        if remaining_transactions == 0 and remaining_items == 0:
            print("\n🎉 Database cleared successfully! Ready for shipping.")
            return True
        else:
            print("\n⚠️  Some data remains. Check the counts above.")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing data: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 olgFeast Database Cleanup")
    print("Preparing database for shipping...")
    print()
    
    success = clear_all_transactions()
    
    if success:
        print("\n✅ Database cleanup completed successfully!")
        print("The database is now clean and ready for shipping.")
    else:
        print("\n❌ Database cleanup failed!")
        print("Please check the errors above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
