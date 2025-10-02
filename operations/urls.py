from django.urls import path, re_path
from . import views

app_name = 'operations'

urlpatterns = [
    # Station displays
    path('stations/', views.station_navigation, name='station_navigation'),
    path('station/<str:station>/', views.station_display, name='station_display'),
    
    # Order management
    path('orders/', views.order_tracking, name='order_tracking'),
    re_path(r'^update-status/(?P<order_id>[-\w]+)/(?P<new_status>[-\w]+)/$', views.update_order_status, name='update_order_status'),
    
    # API endpoints
    path('api/orders/<int:order_id>/status/', views.api_update_order_status, name='api_update_order_status'),
    
    # Analytics dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
