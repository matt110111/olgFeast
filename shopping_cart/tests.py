from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import Profile
from shop_front.models import FoodItem
from shopping_cart.models import Inventory, Item, Transaction


class ShoppingCartTestCase(TestCase):
    """Test shopping cart functionality"""
    
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
        
        self.burger = FoodItem.objects.create(
            food_group='Main',
            name='Test Burger',
            value=12.99,
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
    
    def test_order_tracking_page(self):
        """Test order tracking page loads"""
        self.client.login(username='testuser', password='testpass123')
        
        profile = Profile.objects.get(user=self.user)
        Transaction.objects.create(
            owner=profile,
            ref_code='TEST123456',
            status='pending'
        )
        
        response = self.client.get(reverse('shopping_cart:order_tracking'))
        self.assertEqual(response.status_code, 200)
    
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
        response = self.client.get(reverse('shopping_cart:update_order_status',
                                         args=[transaction.id, 'preparing']))
        self.assertEqual(response.status_code, 302)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'preparing')
