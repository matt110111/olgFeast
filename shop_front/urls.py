from django.urls import path
from .views import (
	ItemCreateView, 
	ItemDetailView,
	ItemUpdateView
)

from . import views


app_name = 'shop_front'

urlpatterns = [
    path('', views.root, name='shop_front-root'),
    path('shop/', views.home, name='shop_front-home'),
    path('shop/detail/<group>', views.detail, name='shop_front-detail_list'),
    path('shop/item/detail/',ItemDetailView.as_view(), name='item-detail'),
    path('shop/item/new/', ItemCreateView.as_view(), name='item-create'),
    path('shop/item/<int:pk>/update/', ItemUpdateView.as_view(), name='item-update'),
    ]