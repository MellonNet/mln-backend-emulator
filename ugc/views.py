from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import FactoryModelForm, GalleryImageForm
from .models import FactoryModel, GalleryImage

@login_required
def search_all_data(request):
	"""
	Get all gallery images by the requesting user.
	Requested in the private view for the collections tab and by the module editor to choose an image.
	"""
	return render(request, "ugc/search_all_data.xml")

def search_all_data_gallery_item(request):
	"""
	Get data of a specific gallery image.
	Requested by gallery modules to display data.
	"""
	return render(request, "ugc/search_all_data_gallery_item.xml", {"image": GalleryImage.objects.get(id=int(request.GET["modelid"]))})

@login_required
def search_factory_item_list(request):
	"""
	Get all factory models by the requesting user.
	Requested in the private view for the collections tab and by the module editor to choose a model.
	"""
	return render(request, "ugc/search_factory_item_list.xml")

def search_factory_item(request):
	"""
	Get data of a specific factory model.
	Requested by factory modules to display data.
	"""
	return render(request, "ugc/search_factory_item.xml", {"model": FactoryModel.objects.get(id=int(request.GET["modelid"]))})


@login_required
def gallery(request):
	"""Gallery image upload interface."""
	if request.method == "POST":
		form = GalleryImageForm(request.POST, request.FILES)
		if form.is_valid():
			obj = form.save(commit=False)
			obj.owner = request.user
			obj.save()
	else:
		form = GalleryImageForm()
	return render(request, "ugc/gallery.html", {"form": form})

@login_required
def factory(request):
	"""Factory model upload interface."""
	if request.method == "POST":
		form = FactoryModelForm(request.POST, request.FILES)
		if form.is_valid():
			obj = form.save(commit=False)
			obj.owner = request.user
			obj.save()
	else:
		form = FactoryModelForm()
	return render(request, "ugc/factory.html", {"form": form})
