from django.shortcuts import render
from accounts.models import Profile
from random import choice
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection


# Create your views here.

from shop_front.models import FoodItem
from shopping_cart.models import Item, Inventory, Transaction

def get_user_pending_order(request):
    # get order for the correct user

    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    if user_inventory:
        # get the only order in the list of filtered orders
        return user_inventory.item_set.all()
    return 0

def order_details(request, **kwargs):
    existing_order = get_user_pending_order(request)

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
    
    return redirect(reverse('shopping_cart:transaction'))

def success(request):
    return redirect(reverse('shop_front:shop_front-home-checkout', args="1"))

def update_Transaction_history(request):
    list_char='abcdefghijklmnopqrstuvxyz1234567890'
    list_char= [letter for letter in list_char]
    ref_code = ''.join([choice(list_char) for i in range(16)])
    user_Profile = get_object_or_404(Profile, user=request.user)
    transaction = Transaction(owner=user_Profile,ref_code=ref_code)
    transaction.save()
    user_items = []
    for item in get_object_or_404(Profile, user=request.user).inventory.item_set.all():
        f_item = FoodItem.objects.filter(name=item.name).get()
        transaction.items.add(f_item)
        transaction.save()
        update_quanity(quanity=item.quanity,f_item=f_item)
        # id = Transaction.objects.raw('SELECT id FROM shopping_cart_transaction_items where fooditem_id = %s order by id desc limit 1',[f_item.id])[-1].id
        # test = Transaction.objects.raw('update shopping_cart_transaction_items set food_quanity=%s where id=%s',[item.quanity,id])
    transaction.save()
    #print(Transaction.objects.filter(ref_code=ref_code).last().items.all())
    user_Profile.inventory.item_set.all().delete()
    return redirect(reverse('shopping_cart:success'))

	#ref_code = ''.join(choice(choices) for i in range(40)) #40 Random Numbers and Letters

def get_quanity(quanity=1,f_item=0):
    with connection.cursor() as cursor:
        pass

def update_quanity(quanity=1,f_item=0):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM shopping_cart_transaction_items where fooditem_id = %s order by id desc limit 1", [f_item.id])
        id = cursor.fetchone()[0]
        cursor.execute("UPDATE shopping_cart_transaction_items SET food_quanity=%s WHERE id=%s",[quanity,id])
