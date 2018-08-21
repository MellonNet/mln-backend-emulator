"""
Base URL registry.
Registered urls are: MLN core, UGC (gallery & factory service and web interface), creation lab (very similar to UGC), standard account management + signup form, django admin interface.
In debug mode django's staticfiles server is also registered, in production this should be handled by a proper HTML server with staticfiles optimizations.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView

urlpatterns = [
	path("mln/", include("mln.urls")),
	path("ugc/", include("ugc.urls")),
	path("ugc", lambda *args, **kwargs: None, name="ugc"),
	path("creation_lab/", include("creation_lab.urls")),
	path("creation_lab", lambda *args, **kwargs: None, name="creation_lab"),
	path("accounts/", include("django.contrib.auth.urls")),
	path("accounts/sign_up", CreateView.as_view(
		template_name="registration/sign_up.html",
		form_class=UserCreationForm,
		success_url="login"
	), name="sign_up"),
	path("admin/", admin.site.urls),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
