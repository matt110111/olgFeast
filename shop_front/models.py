from django.db import models
from django.urls import reverse


class FoodItem(models.Model):
    food_group = models.CharField(max_length=40)
    name = models.CharField(max_length=40)
    value = models.FloatField(default=0.0)
    ticket = models.IntegerField(default=1)

    def get_absolute_url(self):
        return reverse('shop_front:shop_front-home')