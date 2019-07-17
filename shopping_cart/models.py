from django.db import models
from django.contrib.auth.models import User


from accounts.models import Profile
from  shop_front.models import FoodItem

class Inventory(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE)

    def __str__(self):
   		return f'{self.user}'

class Item(models.Model):
    food_group = models.CharField(max_length=40)
    name = models.CharField(max_length=40)
    description = models.TextField(max_length=200, null=True)
    value = models.FloatField(default=0.0)
    ticket = models.IntegerField(default=1)
    quanity = models.IntegerField(default=1)
    invetory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    

    def __str__(self):
    	return f'{self.name}'

 
class Transaction(models.Model):
    ref_code = models.CharField(max_length=40)
    owner = models.OneToOneField(Profile, on_delete=models.CASCADE)
    date_ordered = models.DateTimeField(auto_now=False, auto_now_add=True)
    items = models.ManyToManyField(FoodItem)


    def get_total_tickets(self):
        total = 0
        for item in items:
            total += item.value
        return total


