from ..utils import *

class Question(models.Model):
	"""A question for the "About me" section."""
	text = models.CharField(max_length=64)
	mandatory = models.BooleanField()

	def __str__(self):
		return self.text

class Answer(models.Model):
	"""An answer to an "About me" question."""
	question = models.ForeignKey(Question, related_name="+", on_delete=models.CASCADE)
	text = models.CharField(max_length=64)

	def __str__(self):
		return self.text
