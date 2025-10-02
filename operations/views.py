from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import timedelta
import json

from accounts.models import Profile
from shopping_cart.models import Transaction
from shop_front.models import FoodItem


def station_display(request, station):
    """Display orders for specific kitchen stations"""
    if station not in ['pending', 'preparing', 'ready']:
        return redirect('shop_front:shop_front-home')
    
    # Get orders for this station
    orders = Transaction.objects.filter(status=station).order_by('date_ordered')
    
    # Group orders by time for better display
    recent_orders = orders[:20]  # Show last 20 orders
    
    context = {
        'station': station,
        'station_title': station.title(),
        'orders': recent_orders,
        'order_count': orders.count(),
    }
    
    return render(request, 'operations/station_display.html', context)


def station_navigation(request):
    """Navigation page for station displays"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access station displays.")
        return redirect('shop_front:shop_front-home')
    
    # Get order counts for each station
    pending_count = Transaction.objects.filter(status='pending').count()
    preparing_count = Transaction.objects.filter(status='preparing').count()
    ready_count = Transaction.objects.filter(status='ready').count()
    
    context = {
        'pending_count': pending_count,
        'preparing_count': preparing_count,
        'ready_count': ready_count,
    }
    
    return render(request, 'operations/station_navigation.html', context)


def admin_dashboard(request):
    """Comprehensive admin dashboard with analytics"""
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access the dashboard.")
        return redirect('shop_front:shop_front-home')
    
    # Time filters
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Basic statistics
    total_orders = Transaction.objects.count()
    orders_today = Transaction.objects.filter(date_ordered__gte=last_24h).count()
    orders_this_week = Transaction.objects.filter(date_ordered__gte=last_7d).count()
    orders_this_month = Transaction.objects.filter(date_ordered__gte=last_30d).count()
    
    # Order status distribution
    status_counts = Transaction.objects.values('status').annotate(count=Count('id')).order_by('status')
    
    # User activity statistics
    user_stats = []
    users = Profile.objects.all()
    for user in users:
        user_orders = Transaction.objects.filter(owner=user)
        if user_orders.exists():
            avg_order_time = []
            for order in user_orders.filter(status='complete'):
                total_time = order.get_total_order_time()
                if total_time:
                    avg_order_time.append(total_time)
            
            user_stats.append({
                'username': user.user.username,
                'total_orders': user_orders.count(),
                'orders_today': user_orders.filter(date_ordered__gte=last_24h).count(),
                'avg_order_time': round(sum(avg_order_time) / len(avg_order_time), 2) if avg_order_time else 0,
                'last_order': user_orders.order_by('-date_ordered').first().date_ordered if user_orders.exists() else None,
                'total_spent': sum(order.get_total_value() for order in user_orders),
                'total_tickets': sum(order.get_total_tickets() for order in user_orders)
            })
    
    # Sort users by activity
    user_stats.sort(key=lambda x: x['total_orders'], reverse=True)
    
    # Item popularity statistics
    item_stats = []
    for item in FoodItem.objects.all():
        item_orders = Transaction.objects.filter(items=item)
        item_stats.append({
            'name': item.name,
            'food_group': item.food_group,
            'times_ordered': item_orders.count(),
            'revenue': item_orders.count() * item.value,
            'tickets': item_orders.count() * item.ticket
        })
    
    # Sort by popularity
    item_stats.sort(key=lambda x: x['times_ordered'], reverse=True)
    
    # Timing analytics
    completed_orders = Transaction.objects.filter(status='complete')
    timing_stats = {
        'avg_time_to_preparing': 0,
        'avg_time_to_ready': 0,
        'avg_time_to_complete': 0,
        'avg_total_time': 0,
        'total_completed': completed_orders.count()
    }
    
    if completed_orders.exists():
        times_to_preparing = [o.get_time_to_preparing() for o in completed_orders if o.get_time_to_preparing()]
        times_to_ready = [o.get_time_to_ready() for o in completed_orders if o.get_time_to_ready()]
        times_to_complete = [o.get_time_to_complete() for o in completed_orders if o.get_time_to_complete()]
        total_times = [o.get_total_order_time() for o in completed_orders if o.get_total_order_time()]
        
        timing_stats.update({
            'avg_time_to_preparing': round(sum(times_to_preparing) / len(times_to_preparing), 2) if times_to_preparing else 0,
            'avg_time_to_ready': round(sum(times_to_ready) / len(times_to_ready), 2) if times_to_ready else 0,
            'avg_time_to_complete': round(sum(times_to_complete) / len(times_to_complete), 2) if times_to_complete else 0,
            'avg_total_time': round(sum(total_times) / len(total_times), 2) if total_times else 0,
        })
    
    # Recent activity
    recent_orders = Transaction.objects.order_by('-date_ordered')[:10]
    
    # Revenue statistics
    total_revenue = sum(order.get_total_value() for order in Transaction.objects.filter(status='complete'))
    revenue_today = sum(order.get_total_value() for order in Transaction.objects.filter(status='complete', date_ordered__gte=last_24h))
    revenue_this_week = sum(order.get_total_value() for order in Transaction.objects.filter(status='complete', date_ordered__gte=last_7d))
    
    # Hourly activity for today
    hourly_activity = []
    for hour in range(24):
        hour_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        if hour_start <= now:
            orders_in_hour = Transaction.objects.filter(
                date_ordered__gte=hour_start,
                date_ordered__lt=hour_end
            ).count()
            hourly_activity.append({'hour': hour, 'orders': orders_in_hour})
    
    context = {
        'total_orders': total_orders,
        'orders_today': orders_today,
        'orders_this_week': orders_this_week,
        'orders_this_month': orders_this_month,
        'status_counts': status_counts,
        'user_stats': user_stats[:10],  # Top 10 users
        'item_stats': item_stats[:10],  # Top 10 items
        'timing_stats': timing_stats,
        'recent_orders': recent_orders,
        'total_revenue': round(total_revenue, 2),
        'revenue_today': round(revenue_today, 2),
        'revenue_this_week': round(revenue_this_week, 2),
        'hourly_activity': hourly_activity,
        'status_counts_json': json.dumps(list(status_counts)),
        'hourly_activity_json': json.dumps(hourly_activity),
    }
    
    return render(request, 'operations/admin_dashboard.html', context)


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
    
    return render(request, 'operations/order_tracking.html', context)


def update_order_status(request, order_id, new_status):
    """Update order status (admin only)"""
    if not request.user.is_staff:
        return redirect('operations:order_tracking')
    
    try:
        order = Transaction.objects.get(id=order_id)
        old_status = order.status
        order.status = new_status
        
        # Track timing data
        now = timezone.now()
        if new_status == 'preparing' and old_status == 'pending':
            order.date_preparing = now
        elif new_status == 'ready' and old_status == 'preparing':
            order.date_ready = now
        elif new_status == 'complete' and old_status == 'ready':
            order.date_complete = now
            
        order.save()
        
        # Send WebSocket notification
        send_order_status_notification(order, old_status, new_status)
        
        messages.success(request, f"Order {order.ref_code} status updated to {new_status}")
    except Transaction.DoesNotExist:
        messages.error(request, "Order not found")
    
    return redirect('operations:order_tracking')


@csrf_exempt
@require_http_methods(["POST"])
def api_update_order_status(request, order_id):
    """API endpoint for updating order status with WebSocket notifications"""
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if not new_status or new_status not in ['pending', 'preparing', 'ready', 'complete']:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        order = Transaction.objects.get(id=order_id)
        old_status = order.status
        order.status = new_status
        
        # Track timing data
        now = timezone.now()
        if new_status == 'preparing' and old_status == 'pending':
            order.date_preparing = now
        elif new_status == 'ready' and old_status == 'preparing':
            order.date_ready = now
        elif new_status == 'complete' and old_status == 'ready':
            order.date_complete = now
            
        order.save()
        
        # Send WebSocket notification
        send_order_status_notification(order, old_status, new_status)
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'ref_code': order.ref_code,
            'old_status': old_status,
            'new_status': new_status
        })
        
    except Transaction.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def send_order_status_notification(order, old_status, new_status):
    """Send WebSocket notification for order status changes"""
    try:
        channel_layer = get_channel_layer()
        
        # Prepare order data
        order_data = {
            'id': order.id,
            'ref_code': order.ref_code,
            'customer_name': order.customer_name or order.owner.user.username,
            'date_ordered': order.date_ordered.isoformat(),
            'status': order.status,
            'items': [
                {
                    'name': item.name,
                    'ticket': item.ticket,
                    'value': float(item.value)
                }
                for item in order.items.all()
            ],
            'total_tickets': order.get_total_tickets(),
            'total_value': float(order.get_total_value()),
            'item_count': order.items.count()
        }
        
        # Notify all relevant station groups
        stations_to_notify = [old_status, new_status]
        for station in stations_to_notify:
            if station in ['pending', 'preparing', 'ready']:
                async_to_sync(channel_layer.group_send)(
                    f'kitchen_{station}',
                    {
                        'type': 'order_status_change',
                        'order_id': order.id,
                        'old_status': old_status,
                        'new_status': new_status,
                        'order': order_data
                    }
                )
        
        # Also send a general order update
        async_to_sync(channel_layer.group_send)(
            f'kitchen_{new_status}',
            {
                'type': 'order_update',
                'order': order_data,
                'action': 'status_changed'
            }
        )
    except Exception as e:
        # WebSocket notification failed, but don't break the main functionality
        print(f"WebSocket notification failed: {e}")
        pass
