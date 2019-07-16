from django.shortcuts import render, get_object_or_404


from .models import Profile



def my_profile(request):
	my_user_profile = Profile.objects.filter(user=request.user).first()
	my_orders = Profile.objects.filter(user=request.user).get().inventory.item_set.all()
	context = {
		'my_orders': my_orders
	}
	print(my_orders)
	return render(request, "accounts/profile.html", context)