from ..utils import *

class Color(models.Model):
	"""A color, used for page and module backgrounds."""
	color = models.IntegerField()

	def __str__(self):
		return hex(self.color)
