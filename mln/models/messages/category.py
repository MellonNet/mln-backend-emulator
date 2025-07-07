from ..utils import *

class MessageBodyCategory(models.Model):
	"""A category used for grouping message bodies in the "compose message" interface."""
	name = models.CharField(max_length=32)
	hidden = models.BooleanField()
	background_color = models.IntegerField()
	button_color = models.IntegerField()
	text_color = models.IntegerField()

	class Meta:
		verbose_name_plural = "Message body categories"

	def __str__(self):
		return self.name
