import zipfile

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from ugc_base import clean_file

class GalleryImage(models.Model):
	"""A gallery image, with associated title and description."""
	owner = models.ForeignKey(User, related_name="gallery_images", on_delete=models.CASCADE)
	title = models.CharField(max_length=64)
	description = models.CharField(max_length=64)
	image = models.ImageField(upload_to="gallery_images")

	def __str__(self):
		return self.title

class FactoryModel(models.Model):
	"""A factory model (.lxf), with associated title, description and image."""
	owner = models.ForeignKey(User, related_name="factory_models", on_delete=models.CASCADE)
	title = models.CharField(max_length=64)
	description = models.CharField(max_length=64)
	model = models.FileField(upload_to="factory/models")
	image = models.ImageField(upload_to="factory/images")

	def __str__(self):
		return self.title

clean_file(GalleryImage, "image")
clean_file(FactoryModel, "image")
clean_file(FactoryModel, "model")

@receiver(pre_save, sender=FactoryModel)
def extract_factory_image(sender, instance, **kwargs):
	"""When a .lxf is uploaded, open it and extract the contained thumbnail to be used as the model's associated image.	"""
	if "/" in instance.model.name:
		return False

	with zipfile.ZipFile(instance.model) as lxf:
		instance.image.save(instance.model.name+".png", ContentFile(lxf.read("IMAGE100.PNG")), save=False)
