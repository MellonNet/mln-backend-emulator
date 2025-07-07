from django.urls import path

from . import views

urlpatterns = [
	path("UserCreations", views.user_creations),
	path("Creation", views.creation),
	path("creation_lab_upload", views.creation_lab_upload, name="creation_lab_upload"),
]
