"""
Views.
This is only for HTML pages, for webservice XML handling see the webservice module.
If you're working on views for gallery, factory, creation lab or other related systems, please put them into their own django app. This file is only for the core MLN views.
"""
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def private_view(request):
	"""MLN's private view. Only available for logged in users."""
	return render(request, "mln/private_view.html")

def public_view(request, page_owner_name):
	"""MLN's public view."""
	if page_owner_name == "Default":
		if request.user.is_authenticated:
			return redirect("public_view", request.user.username)
		return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))
	get_object_or_404(User, username=page_owner_name)
	return render(request, "mln/public_view.html", {"page_owner_name": page_owner_name})
