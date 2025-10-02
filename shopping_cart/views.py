from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import Profile
from random import choice
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from shop_front.models import FoodItem
from .models import Item, Transaction


# Create your views here.

def get_user_pending_order(request):
    # get order for the correct user
    if not request.user.is_authenticated:
        return []
    
    user_inventory = get_object_or_404(Profile, user=request.user).inventory
    if user_inventory:
        # get the only order in the list of filtered orders
        return user_inventory.item_set.all()
    return []
    
def order_details(request, **kwargs):
    existing_order = get_user_pending_order(request)

    # Calculate total tickets and total cost
    total_tickets = 0
    total_cost = 0
    for item in existing_order:
        total_tickets += item.ticket * item.quantity
        total_cost += item.value * item.quantity

    context = {
        'order': existing_order,
        'total': total_tickets,
        'total_cost': round(total_cost, 2)
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
    
    # Get customer name from session
    customer_name = request.session.get('customer_name', '')
    if not customer_name:
        # Fallback to username if no customer name provided
        customer_name = request.user.username
    
    transaction = Transaction(owner=user_Profile, ref_code=ref_code, customer_name=customer_name, status='pending')
    transaction.save()
    
    # Clear the customer name from session
    if 'customer_name' in request.session:
        del request.session['customer_name']
    
    user_items = []
    for item in get_object_or_404(Profile, user=request.user).inventory.item_set.all():
        f_item = FoodItem.objects.filter(name=item.name).get()
        # Add the item multiple times based on quantity
        for i in range(item.quantity):
            transaction.items.add(f_item)
    
    # Save to calculate totals
    transaction.save()
    
    # Send WebSocket notification for new order
    send_new_order_notification(transaction)
    
    # Clear user's cart
    user_Profile.inventory.item_set.all().delete()
    return redirect(reverse('shopping_cart:success'))

# Removed get_quantity and update_quantity functions as they were causing database errors
# The transaction process now handles quantities by adding items multiple times

def customer_checkout_form(request):
    """Display customer name input form before checkout"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get user's pending order
    existing_order = get_user_pending_order(request)
    
    if not existing_order:
        messages.info(request, "Your cart is empty. Add some items before checkout.")
        return redirect('shop_front:shop_front-home')
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        if customer_name:
            # Store the customer name in session for checkout
            request.session['customer_name'] = customer_name
            return redirect('shopping_cart:transaction')
        else:
            messages.error(request, "Please enter your name for the order.")
    
    context = {
        'order': existing_order,
        'total': sum(item.ticket * item.quantity for item in existing_order)
    }
    
    return render(request, 'shopping_cart/customer_checkout_form.html', context)


def send_new_order_notification(transaction):
    """Send WebSocket notification for new orders"""
    try:
        channel_layer = get_channel_layer()
        
        # Prepare order data
        order_data = {
            'id': transaction.id,
            'ref_code': transaction.ref_code,
            'customer_name': transaction.customer_name or transaction.owner.user.username,
            'date_ordered': transaction.date_ordered.isoformat(),
            'status': transaction.status,
            'items': [
                {
                    'name': item.name,
                    'ticket': item.ticket,
                    'value': float(item.value)
                }
                for item in transaction.items.all()
            ],
            'total_tickets': transaction.get_total_tickets(),
            'total_value': float(transaction.get_total_value()),
            'item_count': transaction.items.count()
        }
        
        # Notify the pending station
        async_to_sync(channel_layer.group_send)(
            'kitchen_pending',
            {
                'type': 'order_update',
                'order': order_data,
                'action': 'new_order'
            }
        )
    except Exception as e:
        # WebSocket notification failed, but don't break the main functionality
        print(f"WebSocket notification failed: {e}")
        pass

