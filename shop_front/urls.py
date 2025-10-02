from django.urls import path
from .views import (
	ItemCreateView, 
	ItemDetailView,
	ItemUpdateView,
	delete_item
)

from . import views


app_name = 'shop_front'

urlpatterns = [
    path('', views.root, name='shop_front-root'),
    path('shop/', views.home, name='shop_front-home'),
    path('shop/<checkout_status>', views.home, name='shop_front-home-checkout'),
    path('shop/<group>/', views.detail, name='shop_front-detail_list'),
    path('shop/detail/<group>', views.detail, name='shop_front-detail_list-alt'),
    path('shop/item/detail/',ItemDetailView.as_view(), name='item-detail'),
    path('shop/item/new/', ItemCreateView.as_view(), name='item-create'),
    path('shop/item/<int:pk>/update/', ItemUpdateView.as_view(), name='item-update'),
    path('shop/item/<int:pk>/delete/', delete_item, name='item-delete'),
    path('menu/', views.customer_browse, name='customer-browse'),
    path('menu/<group>/', views.customer_detail, name='customer-detail'),
    ]