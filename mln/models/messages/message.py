from ..utils import *
from ..items import *

from .body import *

class Message(models.Model):
	"""
	A message sent from one user to another.
	User messages can only be sent to friends, while messages sent by networkers don't have this restriction.
	Message contents are determined by a prefabricated message text that can be chosen.
	In the case of replies, the original message is also stored, so that the subject can be displayed as RE: <original>.
	Messages can have attachments.
	"""
	sender = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
	recipient = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
	body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)
	reply_body = models.ForeignKey(MessageBody, null=True, blank=True, related_name="+", on_delete=models.CASCADE)
	is_read = models.BooleanField(default=False)

	def __str__(self):
		if self.reply_body_id is not None:
			subject = "RE: "+self.reply_body.subject
		else:
			subject = self.body.subject
		return "Message from %s to %s, subject \"%s\", is read: %s" % (self.sender, self.recipient, subject, self.is_read)

class Attachment(Stack):
	"""An attachment, a stack sent with a message."""
	message = models.ForeignKey(Message, related_name="attachments", on_delete=models.CASCADE)

	class Meta:
		constraints = (models.UniqueConstraint(fields=("message", "item"), name="attachment_unique_message_item"),)

	def __str__(self):
		return "%s attached to %s" % (super().__str__(), self.message)
