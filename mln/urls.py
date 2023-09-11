"""
MLN's registered URLs and their mapping to views.
MLN's original URLs were /PrivateView/Default.aspx and /PublicView/<page_owner_name>.aspx .
Since this server doesn't use aspx, I've changed the URLs to /private_view/default and /public_view/<page_owner_name> and redirected the old ones.
There are a few more entries in here because the flash files aren't always consistent in the URLs they request.
"""
from django.urls import path
from django.shortcuts import redirect

from .views import ui
from .views.api.xml import webservice

urlpatterns = [
	path("", lambda x: redirect("private_view/default")),
	path("status.aspx", lambda x: redirect("login")), # login prompt when clicking on page while not logged in
	path("private_view/default", ui.private_view, name="private_view"),
	path("PrivateView/Default.aspx", lambda x: redirect("private_view")),
	path("public_view/<str:page_owner_name>", ui.public_view, name="public_view"),
	path("PublicView/<str:page_owner_name>.aspx", lambda x, page_owner_name: redirect("public_view", page_owner_name)),
	path("Publicview/<str:page_owner_name>.aspx", lambda x, page_owner_name: redirect("public_view", page_owner_name)),
	path("Publicview/<str:page_owner_name>.html", lambda x, page_owner_name: redirect("public_view", page_owner_name)), # click on friend in friend list
	path("webservice", webservice.webservice, name="webservice"),
]
