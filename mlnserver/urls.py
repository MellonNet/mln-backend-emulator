"""
Base URL registry.
Registered urls are: MLN core, UGC (gallery & factory service and web interface), creation lab (very similar to UGC), standard account management + signup form, django admin interface.
In debug mode django's staticfiles server is also registered, in production this should be handled by a proper HTML server with staticfiles optimizations.
"""
from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import PasswordChangeView
from django.views.generic.edit import CreateView

def flashvars_handler(request):
	raise Http404("""
	Page is not intended to be viewed, only serves as root for flashvars.
	Contact the server operator if you did not intend to get here.""")

urlpatterns = [
	path("", lambda x: redirect("mln/private_view/default")),
	path("mln/", include("mln.urls")),
	path("ugc/", include("ugc.urls")),
	path("ugc", flashvars_handler, name="ugc"),
	path("creation_lab/", include("creation_lab.urls")),
	path("creation_lab", flashvars_handler, name="creation_lab"),
	path("accounts/", include("django.contrib.auth.urls")),
	path("accounts/sign_up", CreateView.as_view(
		template_name="registration/sign_up.html",
		form_class=UserCreationForm,
		success_url="login"
	), name="sign_up"),
	path("accounts/password_change", PasswordChangeView.as_view()),
	path("admin/", admin.site.urls),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
