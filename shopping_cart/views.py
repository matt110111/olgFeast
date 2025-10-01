from django.shortcuts import render
from accounts.models import Profile
from random import choice
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from django.contrib import messages
from shop_front.models import FoodItem
from .models import Item, Transaction


# Create your views here.

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
    try:
        # get the user profile
        user_inventory = get_object_or_404(Profile, user=request.user).inventory
        
        # translate the item_id from request to FoodItem
        item_id = kwargs.get('item_id', "")
        try:
            product = FoodItem.objects.get(id=item_id)
        except FoodItem.DoesNotExist:
            messages.error(request, f"Item with ID {item_id} not found.")
            return redirect(reverse('shop_front:shop_front-home'))
        except ValueError:
            messages.error(request, "Invalid item ID.")
            return redirect(reverse('shop_front:shop_front-home'))

        # check if item is in user_inventory - if it is update the quantity, if not add item to inventory
        existing_item = user_inventory.item_set.filter(name=product.name).first()
        
        if not existing_item:
            # Create new item in cart
            item = Item(
                food_group=product.food_group,
                name=product.name,
                value=product.value,
                ticket=product.ticket,
                inventory=user_inventory,
                quantity=1
            )
            item.save()
            messages.success(request, f"{product.name} added to cart!")
        else:
            # Update existing item quantity
            existing_item.quantity += 1
            existing_item.save()
            messages.success(request, f"{product.name} quantity updated!")

    except Exception as e:
        messages.error(request, f"Error adding item to cart: {str(e)}")
        return redirect(reverse('shop_front:shop_front-home'))

    return redirect(reverse('shop_front:shop_front-home'))


def manipulate_quantity(request, **kwargs):
    try:
        user_inventory = get_object_or_404(Profile, user=request.user).inventory
        item_id = kwargs.get('item_id', "")
        direction = kwargs.get('direction', "")
        
        try:
            item = user_inventory.item_set.get(id=item_id)
        except Item.DoesNotExist:
            messages.error(request, "Item not found in cart.")
            return redirect(reverse('shopping_cart:order_summary'))

        if direction == 'up':
            quantity = 1
        else:
            quantity = -1
        
        item.quantity += quantity
        
        # Don't allow negative quantities
        if item.quantity <= 0:
            item.delete()
            messages.success(request, f"{item.name} removed from cart.")
        else:
            item.save()
            messages.success(request, f"{item.name} quantity updated.")
            
    except Exception as e:
        messages.error(request, f"Error updating item quantity: {str(e)}")
    
    return redirect(reverse('shopping_cart:order_summary'))

def delete_item(request, **kwargs):
    try:
        user_inventory = get_object_or_404(Profile, user=request.user).inventory
        item_id = kwargs.get('item_id', "")
        
        try:
            item = user_inventory.item_set.get(id=item_id)
            item_name = item.name
            item.delete()
            messages.success(request, f"{item_name} removed from cart.")
        except Item.DoesNotExist:
            messages.error(request, "Item not found in cart.")
            
    except Exception as e:
        messages.error(request, f"Error removing item: {str(e)}")

    return redirect(reverse('shopping_cart:order_summary'))

def delete_cart(request, **kwargs):
    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    user_inventory.item_set.all().delete()
    return redirect(reverse('shopping_cart:order_summary'))

def checkout(request):
    
    return redirect(reverse('shopping_cart:transaction'))

def success(request):
    # Redirect to home with success message, but also provide link to order tracking
    return redirect(reverse('shop_front:shop_front-home-checkout', args="1"))

def update_Transaction_history(request):
    list_char='abcdefghijklmnopqrstuvxyz1234567890'
    list_char= [letter for letter in list_char]
    ref_code = ''.join([choice(list_char) for i in range(16)])
    user_Profile = get_object_or_404(Profile, user=request.user)
    transaction = Transaction(owner=user_Profile, ref_code=ref_code, status='pending')
    transaction.save()
    
    user_items = []
    for item in get_object_or_404(Profile, user=request.user).inventory.item_set.all():
        f_item = FoodItem.objects.filter(name=item.name).get()
        # Add the item multiple times based on quantity
        for i in range(item.quantity):
            transaction.items.add(f_item)
    
    # Save to calculate totals
    transaction.save()
    
    # Clear user's cart
    user_Profile.inventory.item_set.all().delete()
    return redirect(reverse('shopping_cart:success'))

	#ref_code = ''.join(choice(choices) for i in range(40)) #40 Random Numbers and Letters

# Removed get_quantity and update_quantity functions as they were causing database errors
# The transaction process now handles quantities by adding items multiple times

def order_tracking(request):
    """Display live order tracking page showing all recent orders"""
    # Get recent orders (last 50)
    recent_orders = Transaction.objects.all().order_by('-date_ordered')[:50]
    
    # Get orders by status using database queries
    pending_orders = Transaction.objects.filter(status='pending').order_by('date_ordered')
    preparing_orders = Transaction.objects.filter(status='preparing').order_by('date_ordered')
    ready_orders = Transaction.objects.filter(status='ready').order_by('date_ordered')
    completed_orders = Transaction.objects.filter(status='complete').order_by('-date_ordered')[:20]
    
    context = {
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders,
        'total_orders': Transaction.objects.count(),
    }
    
    return render(request, 'shopping_cart/order_tracking.html', context)

def update_order_status(request, order_id, new_status):
    """Update order status (admin only)"""
    if not request.user.is_staff:
        return redirect('shopping_cart:order_tracking')
    
    try:
        order = Transaction.objects.get(id=order_id)
        order.status = new_status
        order.save()
    except Transaction.DoesNotExist:
        pass
    
    return redirect('shopping_cart:order_tracking')
