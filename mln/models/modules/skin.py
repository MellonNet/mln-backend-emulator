from ..utils import *

class ModuleSkin(models.Model):
	"""A skin (background pattern) of a module."""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name
