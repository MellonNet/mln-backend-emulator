from ..utils import *

from .body import *
from .reply import *

class NetworkerMessageTriggerLegacy(models.Model):
	"""Currently meant for devs to collect data on triggers, later to be properly integrated into the system."""
	networker = models.CharField(max_length=64, blank=True, null=True)
	body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)
	trigger = models.TextField(blank=True, null=True)
	source = models.TextField()
	notes = models.TextField(blank=True, null=True)
	updated = models.ForeignKey(NetworkerReply, related_name="legacy", on_delete=models.SET_NULL, blank=True, null=True)

	def __str__(self):
		return "From %s: %s" % (self.networker, self.body)

class NetworkerMessageAttachmentLegacy(Stack):
	"""A stack to be attached to a networker message."""
	trigger = models.ForeignKey(NetworkerMessageTriggerLegacy, related_name="attachments", on_delete=models.CASCADE)
	updated = models.ForeignKey(MessageTemplateAttachment, related_name="legacy", on_delete=models.CASCADE, blank=True, null=True)

	class Meta:
		constraints = (models.UniqueConstraint(fields=("trigger", "item"), name="networker_message_attachment_unique_trigger_item"),)
