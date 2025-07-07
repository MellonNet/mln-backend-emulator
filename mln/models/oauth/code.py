from ..utils import *
from .client import *

class OAuthCode(models.Model):
	user = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
	auth_code = models.CharField(max_length=64)
	client = models.ForeignKey(OAuthClient, related_name="+", on_delete=models.CASCADE)
	generated_at = models.DateTimeField()

	def __str__(self):
		return f"Auth code for {self.user}"

	class Meta:
		verbose_name_plural = "OAuth Authorization Codes"
