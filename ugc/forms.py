from django import forms
from .models import FactoryModel, GalleryImage

class FactoryModelForm(forms.ModelForm):
	class Meta:
		model = FactoryModel
		fields = ("title", "description", "model")

class GalleryImageForm(forms.ModelForm):
	class Meta:
		model = GalleryImage
		fields = ("title", "description", "image")
