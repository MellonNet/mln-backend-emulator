from django import forms
from .models import CreationLabCreation

class CreationLabCreationForm(forms.ModelForm):
	class Meta:
		model = CreationLabCreation
		fields = ("title", "description", "image")
