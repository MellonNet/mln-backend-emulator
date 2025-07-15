from ..utils import *
from ..items import *

from .template import *
from .body import *

class MessageReplyType(Enum):
	"""
	Message reply options, defining the combinations of reply and easy reply that can be used on a message.
	I'm not sure how these are associated with messages.
	Currently I just set a message to "normal & easy reply" if it has easy replies available, and "normal reply only" if it doesn't.
	"""
	NORMAL_REPLY_ONLY = 0
	NORMAL_AND_EASY_REPLY = 1
	EASY_REPLY_ONLY = 2
	NO_REPLY = 3

class NetworkerReply(models.Model):
	template = models.ForeignKey(MessageTemplate, related_name="+", on_delete=models.CASCADE)
	networker = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE, blank=True, null=True, limit_choices_to={"profile__is_networker": True})
	trigger_body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE, null=True, blank=True)
	trigger_attachment = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, null=True, blank=True)

	class Meta:
		verbose_name_plural = "Networker replies"

	def __str__(self):
		return "Reply when sending %s to %s: %s" % (self.trigger_attachment or self.trigger_body, self.networker, self.template.body.subject)

	def should_reply(self, message, attachment):
		return (
			(self.trigger_body is not None and message.body == self.trigger_body) or
			(self.trigger_attachment is not None and attachment is not None and attachment.item == self.trigger_attachment)
		)

