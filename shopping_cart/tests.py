from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction

from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Inventory, Item, Transaction


class ShoppingCartTestCase(TestCase):
    """Comprehensive shopping cart functionality tests"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test food items
        self.burger = FoodItem.objects.create(
            food_group='Main Course',
            name='Test Burger',
            value=12.99,
            ticket=1
        )
        
        self.pizza = FoodItem.objects.create(
            food_group='Main Course',
            name='Test Pizza',
            value=15.99,
            ticket=2
        )
        
        self.drink = FoodItem.objects.create(
            food_group='Beverage',
            name='Test Drink',
            value=3.99,
            ticket=1
        )
        
        self.client = Client()
    
    def test_add_to_cart(self):
        """Test adding items to cart"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.assertEqual(response.status_code, 302)
        
        profile = Profile.objects.get(user=self.user)
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().name, self.burger.name)
    
    def test_add_multiple_items_to_cart(self):
        """Test adding multiple different items to cart"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add multiple items
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.pizza.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.drink.id]))
        
        profile = Profile.objects.get(user=self.user)
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 3)
    
    def test_add_same_item_multiple_times(self):
        """Test adding the same item multiple times increases quantity"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add same item multiple times
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        
        profile = Profile.objects.get(user=self.user)
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 1)  # Only one item record
        self.assertEqual(items.first().quantity, 3)  # But quantity is 3
    
    def test_cart_summary_page(self):
        """Test cart summary page loads correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add items to cart
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.pizza.id]))
        
        response = self.client.get(reverse('shopping_cart:order_summary'))
        self.assertEqual(response.status_code, 200)
        
        # Check that items are displayed
        self.assertContains(response, self.burger.name)
        self.assertContains(response, self.pizza.name)
    
    def test_quantity_manipulation(self):
        """Test quantity increase and decrease"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add item to cart
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        
        profile = Profile.objects.get(user=self.user)
        item = profile.inventory.item_set.first()
        original_quantity = item.quantity
        
        # Test quantity increase
        response = self.client.get(reverse('shopping_cart:manipulate_quantity', 
                                         args=[item.id, 'up']))
        self.assertEqual(response.status_code, 302)
        
        item.refresh_from_db()
        self.assertEqual(item.quantity, original_quantity + 1)
        
        # Test quantity decrease
        response = self.client.get(reverse('shopping_cart:manipulate_quantity', 
                                         args=[item.id, 'down']))
        self.assertEqual(response.status_code, 302)
        
        item.refresh_from_db()
        self.assertEqual(item.quantity, original_quantity)
    
    def test_item_deletion(self):
        """Test item deletion from cart"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add items to cart
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.pizza.id]))
        
        profile = Profile.objects.get(user=self.user)
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 2)
        
        # Delete one item
        first_item = items.first()
        response = self.client.get(reverse('shopping_cart:delete_item', args=[first_item.id]))
        self.assertEqual(response.status_code, 302)
        
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 1)
    
    def test_cart_clearing(self):
        """Test clearing entire cart"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add items to cart
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.pizza.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.drink.id]))
        
        profile = Profile.objects.get(user=self.user)
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 3)
        
        # Clear cart
        response = self.client.get(reverse('shopping_cart:delete_cart'))
        self.assertEqual(response.status_code, 302)
        
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 0)
    
    def test_checkout_process(self):
        """Test complete checkout process"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add items to cart
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.burger.id]))
        self.client.get(reverse('shopping_cart:add_to_cart', args=[self.pizza.id]))
        
        # Test checkout initiation
        response = self.client.get(reverse('shopping_cart:checkout'))
        self.assertEqual(response.status_code, 302)
        
        # Test transaction creation
        response = self.client.get(reverse('shopping_cart:transaction'))
        self.assertEqual(response.status_code, 302)
        
        # Verify transaction was created
        profile = Profile.objects.get(user=self.user)
        transactions = Transaction.objects.filter(owner=profile)
        self.assertTrue(transactions.exists())
        
        # Verify cart was cleared
        items = profile.inventory.item_set.all()
        self.assertEqual(items.count(), 0)
    
    def test_order_tracking_page(self):
        """Test order tracking page loads"""
        self.client.login(username='testuser', password='testpass123')
        
        profile = Profile.objects.get(user=self.user)
        transaction = Transaction.objects.create(
            owner=profile,
            ref_code='TEST123456',
            status='pending'
        )
        
        response = self.client.get(reverse('operations:order_tracking'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, transaction.ref_code[:8])
    
    def test_order_status_update(self):
        """Test order status update functionality"""
        profile = Profile.objects.get(user=self.user)
        transaction = Transaction.objects.create(
            owner=profile,
            ref_code='TEST123456',
            status='pending'
        )
        
        # Test staff user can update status
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('operations:update_order_status',
                                         args=[transaction.id, 'preparing']))
        self.assertEqual(response.status_code, 302)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'preparing')
    
    def test_order_status_workflow(self):
        """Test complete order status workflow"""
        profile = Profile.objects.get(user=self.user)
        transaction = Transaction.objects.create(
            owner=profile,
            ref_code='WORKFLOW123',
            status='pending'
        )
        
        self.client.login(username='staffuser', password='testpass123')
        
        # Test status transitions
        status_transitions = [
            ('pending', 'preparing'),
            ('preparing', 'ready'),
            ('ready', 'complete')
        ]
        
        for current_status, new_status in status_transitions:
            transaction.status = current_status
            transaction.save()
            
            response = self.client.get(reverse('operations:update_order_status',
                                             args=[transaction.id, new_status]))
            self.assertEqual(response.status_code, 302)
            
            transaction.refresh_from_db()
            self.assertEqual(transaction.status, new_status)
    
    def test_non_staff_cannot_update_status(self):
        """Test that non-staff users cannot update order status"""
        profile = Profile.objects.get(user=self.user)
        transaction = Transaction.objects.create(
            owner=profile,
            ref_code='TEST123456',
            status='pending'
        )
        
        # Test regular user cannot update status
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('operations:update_order_status',
                                         args=[transaction.id, 'preparing']))
        # Should redirect back to order tracking
        self.assertEqual(response.status_code, 302)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'pending')  # Status should not change
    
    def test_transaction_model_methods(self):
        """Test Transaction model methods"""
        profile = Profile.objects.get(user=self.user)
        transaction = Transaction.objects.create(
            owner=profile,
            ref_code='MODELTEST123',
            status='pending'
        )
        
        # Add items to transaction
        transaction.items.add(self.burger)
        transaction.items.add(self.pizza)
        transaction.items.add(self.pizza)  # Add pizza twice (but ManyToMany only stores once)
        transaction.save()
        
        # Test get_item_summary method
        summary = transaction.get_item_summary()
        self.assertIn(self.burger.name, summary)
        self.assertIn(self.pizza.name, summary)
        self.assertEqual(summary[self.burger.name], 1)
        self.assertEqual(summary[self.pizza.name], 1)  # ManyToMany only stores unique items
        
        # Test total calculations
        expected_value = self.burger.value + self.pizza.value  # Only one pizza due to ManyToMany
        expected_tickets = self.burger.ticket + self.pizza.ticket  # Only one pizza due to ManyToMany
        
        self.assertEqual(transaction.total_value, expected_value)
        self.assertEqual(transaction.total_tickets, expected_tickets)
    
    def test_invalid_item_id_handling(self):
        """Test handling of invalid item IDs"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with non-existent item ID
        response = self.client.get(reverse('shopping_cart:add_to_cart', args=[99999]))
        self.assertEqual(response.status_code, 302)  # Should redirect with error
    
    def test_invalid_transaction_id_handling(self):
        """Test handling of invalid transaction IDs"""
        self.client.login(username='staffuser', password='testpass123')
        
        # Test with non-existent transaction ID
        response = self.client.get(reverse('operations:update_order_status',
                                         args=[99999, 'preparing']))
        self.assertEqual(response.status_code, 302)  # Should redirect back
