from ..utils import *
from .client import *

class OAuthToken(models.Model):
	access_token = models.CharField(max_length=64)
	user = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
	client = models.ForeignKey(OAuthClient, related_name="+", on_delete=models.CASCADE)

	def __str__(self):
		return f"OAuth access token for {self.user}"

	class Meta:
		verbose_name_plural = "OAuth Tokens"
