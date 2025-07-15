from ..utils import *
from ..items import *

from .body import *

class MessageTemplate(models.Model):
	"""
	Defines a template for a message that will be sent by MLN.
	These templates can have attachments, but not a recipient.
	These are different from [Message], in that the latter have already been sent.
	"""
	body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)

	def __str__(self):
		result = self.body.subject
		for attachment in self.attachments.all():
			result += " + %s" % str(attachment)
		return result

class MessageTemplateAttachment(Stack):
	"""An attachment for a [MessageTemplate]."""
	template = models.ForeignKey(MessageTemplate, related_name="attachments", on_delete=models.CASCADE)

	class Meta:
		constraints = (models.UniqueConstraint(fields=("template", "item"), name="messsage_template_attachment_unique_template_item"),)
