from django.urls import path

from .views import my_profile

app_name = 'accounts'

urlpatterns = [
	path('profile/', my_profile, name='my_profile')
]