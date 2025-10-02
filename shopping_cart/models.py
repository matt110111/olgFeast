from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Profile
from  shop_front.models import FoodItem

class Inventory(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE)

    def __str__(self):
   		return f'{self.user}'

# Signal to create Inventory when Profile is created
@receiver(post_save, sender=Profile)
def create_profile_inventory(sender, instance, created, **kwargs):
    if created:
        Inventory.objects.create(user=instance)

@receiver(post_save, sender=Profile)
def save_profile_inventory(sender, instance, **kwargs):
    if hasattr(instance, 'inventory'):
        instance.inventory.save()

class Item(models.Model):
    food_group = models.CharField(max_length=40)
    name = models.CharField(max_length=40)
    description = models.TextField(max_length=200, null=True)
    value = models.FloatField(default=0.0)
    ticket = models.IntegerField(default=1)
    quantity = models.IntegerField(default=1)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    

    def __str__(self):
    	return f'{self.name}'

 
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('complete', 'Complete'),
    ]
    
    ref_code = models.CharField(max_length=40)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    date_ordered = models.DateTimeField(auto_now=False, auto_now_add=True)
    items = models.ManyToManyField(FoodItem)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timing fields for analytics
    date_preparing = models.DateTimeField(null=True, blank=True)
    date_ready = models.DateTimeField(null=True, blank=True)
    date_complete = models.DateTimeField(null=True, blank=True)
    last_status_change = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.ref_code} - {self.owner.user.username}"

    def get_total_tickets(self):
        total = 0
        for item in self.items.all():
            total += item.ticket
        return total
    
    def get_total_value(self):
        total = 0
        for item in self.items.all():
            total += item.value
        return total
    
    def get_item_summary(self):
        """Return a summary of items in this order"""
        item_counts = {}
        for item in self.items.all():
            item_counts[item.name] = item_counts.get(item.name, 0) + 1
        return item_counts
    
    @property
    def total_value(self):
        """Return total value of all items in this transaction"""
        return self.get_total_value()
    
    @property
    def total_tickets(self):
        """Return total tickets of all items in this transaction"""
        return self.get_total_tickets()
    
    def get_time_to_preparing(self):
        """Get time from order to preparing status"""
        if self.date_preparing:
            return (self.date_preparing - self.date_ordered).total_seconds() / 60  # minutes
        return None
    
    def get_time_to_ready(self):
        """Get time from preparing to ready status"""
        if self.date_ready and self.date_preparing:
            return (self.date_ready - self.date_preparing).total_seconds() / 60  # minutes
        return None
    
    def get_time_to_complete(self):
        """Get time from ready to complete status"""
        if self.date_complete and self.date_ready:
            return (self.date_complete - self.date_ready).total_seconds() / 60  # minutes
        return None
    
    def get_total_order_time(self):
        """Get total time from order to complete"""
        if self.date_complete:
            return (self.date_complete - self.date_ordered).total_seconds() / 60  # minutes
        return None


