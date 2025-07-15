from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .forms import CreationLabCreationForm
from .models import CreationLabCreation

@login_required
def user_creations(request):
	"""
	Get all creations by the requesting user.
	Requested by the module editor to choose a creation.
	"""
	return render(request, "creation_lab/user_creations.xml")

def creation(request):
	"""
	Get data of a specific creation.
	Requested by pellet inductor modules to display data.
	"""
	return render(request, "creation_lab/creation.xml", {"creation": CreationLabCreation.objects.get(id=int(request.GET["CreationID"]))})


@login_required
def creation_lab_upload(request):
	"""Upload interface."""
	if request.method == "POST":
		form = CreationLabCreationForm(request.POST, request.FILES)
		if form.is_valid():
			obj = form.save(commit=False)
			obj.owner = request.user
			obj.save()
	else:
		form = CreationLabCreationForm()
	return render(request, "creation_lab/creation_lab_upload.html", {"form": form})
