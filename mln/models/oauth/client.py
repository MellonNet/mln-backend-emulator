from ..utils import *

class OAuthClient(models.Model):
	client_id = models.CharField(max_length=64)
	client_name = models.CharField(max_length=64)
	client_secret = models.CharField(max_length=64)
	image_url = models.URLField()

	def __str__(self):
		return self.client_name

	class Meta:
		verbose_name_plural = "OAuth Clients"
