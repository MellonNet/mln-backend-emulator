from django.contrib.auth.models import User
from django.db import models

from ugc_base import clean_file

class CreationLabCreation(models.Model):
	"""
	A creation in the creation lab.
	Implemented are title, description and an image.
	Additional currently unimplemented attributes that are recognized by MLN are a category and a download link.
	"""
	owner = models.ForeignKey(User, related_name="creation_lab_creations", on_delete=models.CASCADE)
	title = models.CharField(max_length=64)
	description = models.CharField(max_length=64)
	image = models.ImageField(upload_to="creation_lab/images")

	def __str__(self):
		return self.title

clean_file(CreationLabCreation, "image")
