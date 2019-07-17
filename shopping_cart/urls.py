from django.conf.urls import url

from . import views

app_name = 'shopping_cart'

urlpatterns = [
    url(r'^add-to-cart/(?P<item_id>[-\w]+)/$', views.add_to_cart, name="add_to_cart"),
    url(r'^order-summary/$', views.order_details, name="order_summary"),
    url(r'^checkout/$', views.checkout, name="checkout"),
    url(r'^success/$', views.success, name="success"),
    url(r'^transacyion/$', views.update_Transaction_history, name="transaction"),
    url(r'^item/quanity/(?P<item_id>[-\w]+)/(?P<direction>[-\w]+)/$', views.manipulate_quanity, name='manipulate_quanity'),
    url(r'^item/delete/(?P<item_id>[-\w]+)/$', views.delete_item, name='delete_item'),
    url(r'^item/delete_cart/$', views.delete_cart, name='delete_cart'),
    ]