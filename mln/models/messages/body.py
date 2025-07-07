from ..utils import *
from .category import *

class MessageBodyType(Enum):
	MODULE = auto()
	ITEM = auto()
	FRIEND = auto()
	REPLY = auto()
	USER = auto()
	SYSTEM = auto()
	BETA = auto()
	INTEGRATION = auto()
	UNPUBLISHED = auto()
	OTHER = auto()

class MessageBody(models.Model):
	"""
	A message text, consisting of subject and body.
	As MLN only allows sending prefabricated messages, using one of these is the only way of communication.
	Messages from Networkers also use this class.
	Some message texts have ready-made responses available, called easy replies.
	A common example is an easy reply of "Thanks", used by various message texts.
	"""
	category = models.ForeignKey(MessageBodyCategory, related_name="+", on_delete=models.CASCADE)
	type = EnumField(MessageBodyType, null=True, blank=True)
	subject = models.CharField(max_length=128)
	text = models.TextField()
	notes = models.TextField(default="", blank=True)
	easy_replies = models.ManyToManyField("self", related_name="+", symmetrical=False, blank=True)

	class Meta:
		ordering = "subject", "text"
		verbose_name_plural = "Message bodies"

	def __str__(self):
		string = "%s: %s" % (self.subject, self.text)
		if len(string) > 100:
			string = string[:97]+"..."
		return string
