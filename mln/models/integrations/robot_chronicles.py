from ..utils import *
from ..messages import *

class RobotChroniclesMessage(models.Model):
	template = models.ForeignKey(MessageTemplate, related_name="+", on_delete=models.CASCADE)
	networker = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE, limit_choices_to={"profile__is_networker": True})
	award = models.IntegerField()

	def __str__(self):
		return f"Rank {self.rank} message"
