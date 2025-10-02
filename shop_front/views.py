from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.generic import (
	CreateView,
	DetailView,
	UpdateView
)

from accounts.models import Profile
from .models import FoodItem



def root(request):
    return render(request, 'shop_front/root.html')

def home(request, checkout_status=0):
	if checkout_status == "1":
		checkout_status =  True
	groups = FoodItem.objects.order_by().values('food_group').distinct()
	context = {
			'checkout' : checkout_status,
			'groups' : groups,
	}
	return render(request, 'shop_front/home.html', context)

def detail(request, group):
	items_to_return = FoodItem.objects.filter(food_group=group)
	context = {
		'items' : items_to_return,
	}
	return render(request, 'shop_front/detail_list.html', context)
class ItemDetailView(DetailView):
	model = FoodItem

class ItemCreateView(CreateView):
	model = FoodItem
	fields = ['food_group','name','value','ticket']

class ItemUpdateView(UpdateView):
	model = FoodItem
	fields = ['food_group','name','value','ticket']

def delete_item(request, pk):
	"""Delete a food item - admin only"""
	if not request.user.is_superuser:
		messages.error(request, "You don't have permission to delete items.")
		return redirect('shop_front:shop_front-home')
	
	item = get_object_or_404(FoodItem, pk=pk)
	item_name = item.name
	item.delete()
	messages.success(request, f"'{item_name}' has been deleted successfully.")
	
	# Redirect back to the food group page if possible
	return redirect('shop_front:shop_front-home')

def customer_browse(request):
    """Customer view for browsing items (no purchase functionality)"""
    groups = FoodItem.objects.order_by().values('food_group').distinct()
    context = {
        'groups': groups,
        'is_customer_view': True,
    }
    return render(request, 'shop_front/customer_browse.html', context)

def customer_detail(request, group):
    """Customer view for item details (no purchase functionality)"""
    items_to_return = FoodItem.objects.filter(food_group=group)
    context = {
        'items': items_to_return,
        'group': group,
        'is_customer_view': True,
    }
    return render(request, 'shop_front/customer_detail.html', context)
