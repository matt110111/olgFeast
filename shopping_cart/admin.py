from django.contrib import admin
from .models import Inventory, Item, Transaction

admin.site.register(Inventory)
admin.site.register(Item)
admin.site.register(Transaction)