from django.urls import path, re_path

from . import views

app_name = 'shopping_cart'

urlpatterns = [
    re_path(r'^add-to-cart/(?P<item_id>[-\w]+)/$', views.add_to_cart, name="add_to_cart"),
    path('order-summary/', views.order_details, name="order_summary"),
    path('checkout/', views.checkout, name="checkout"),
    path('success/', views.success, name="success"),
    path('transacyion/', views.update_Transaction_history, name="transaction"),
    re_path(r'^item/quantity/(?P<item_id>[-\w]+)/(?P<direction>[-\w]+)/$', views.manipulate_quantity, name='manipulate_quantity'),
    re_path(r'^item/delete/(?P<item_id>[-\w]+)/$', views.delete_item, name='delete_item'),
    path('item/delete_cart/', views.delete_cart, name='delete_cart'),
    path('order-tracking/', views.order_tracking, name='order_tracking'),
    re_path(r'^update-status/(?P<order_id>[-\w]+)/(?P<new_status>[-\w]+)/$', views.update_order_status, name='update_order_status'),
    ]