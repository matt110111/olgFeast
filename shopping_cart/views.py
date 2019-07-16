from django.shortcuts import render
from accounts.models import Profile

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404



# Create your views here.

from shop_front.models import FoodItem
from shopping_cart.models import Item, Inventory

def get_user_pending_order(request):
    # get order for the correct user

    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    if user_inventory:
        # get the only order in the list of filtered orders
        return user_inventory.item_set.all()
    return 0

def order_details(request, **kwargs):
    existing_order = get_user_pending_order(request)
    print (existing_order)
    total = 0
    context = {
        'order': existing_order,
        'total': total
    }
    return render(request, 'shopping_cart/order_summary.html', context)

@login_required()
def add_to_cart(request, **kwargs):
    # get the user profile
    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    # translate the item_id from request to FoodItem
    product = FoodItem.objects.filter(id=kwargs.get('item_id', "")).get()
    


    # check if item is user_inventory if it is update the quanity if not add item to inventory
    if not user_inventory.item_set.filter(name=product.name):
        item = Item(food_group=product.food_group,name=product.name,value=product.value,ticket=product.ticket,invetory=user_inventory)
        item.save()
    else:
        item = user_inventory.item_set.all().filter(name=product.name).get()
        item.quanity += 1
        item.save()

    return redirect(reverse('shop_front:shop_front-home'))


def manipulate_quanity(request, **kwargs):
    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    item_id = kwargs.get('item_id', "")
    direction = kwargs.get('direction', "")
    item = user_inventory.item_set.all().filter(id=item_id).get()

    if direction == 'up':
        quanity = 1
    else:
        quanity = -1
    item.quanity += quanity
    item.save()
    return redirect(reverse('shopping_cart:order_summary'))

def delete_item(request, **kwargs):
    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    item_id = kwargs.get('item_id', "")
    user_inventory.item_set.all().filter(id=item_id).get().delete()

    return redirect(reverse('shopping_cart:order_summary'))

def delete_cart(request, **kwargs):
    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    user_inventory.item_set.all().delete()
    return redirect(reverse('shopping_cart:order_summary'))
def checkout(request):
	    return redirect(reverse('shopping_cart:success'))

def success(request):
    return redirect(reverse('shop_front:shop_front-home'))

def update_Transaction_history(request):
	pass

	#ref_code = ''.join(choice(choices) for i in range(40)) #40 Random Numbers and Letters