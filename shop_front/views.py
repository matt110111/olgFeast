from django.shortcuts import render, get_object_or_404
from django.utils import timezone
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
