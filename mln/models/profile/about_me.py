from ..utils import *

from .question import *

class AboutMe(models.Model):
	"""Questions and answers the user can choose to display on their page as a bio/profile of themselves."""
	user = models.OneToOneField(User, related_name="about_me", on_delete=models.CASCADE)

	def __str__(self):
		return "%s's about me" % self.user

	def clean(self):
		provided = set()
		for i in range(6):
			question_id = getattr(self, "question_%i_id" % i)
			answer_id = getattr(self, "answer_%i_id" % i)
			provided.add(question_id)
			if not Answer.objects.filter(id=answer_id, question_id=question_id).exists():
				answer = getattr(self, "answer_%i" % i)
				question = getattr(self, "question_%i" % i)
				raise ValidationError({"answer_%i" % i: "Answer %s is not an answer to Question %s" % (answer, question)})
		if len(provided) != 6:
			raise ValidationError("Duplicate questions provided")
		for question in Question.objects.filter(mandatory=True):
			if question.id not in provided:
				raise ValidationError("Mandatory question %s not provided" % question)

for i in range(6):
	AboutMe.add_to_class("question_%i" % i, models.ForeignKey(Question, related_name="+", on_delete=models.PROTECT))
	AboutMe.add_to_class("answer_%i" % i, models.ForeignKey(Answer, related_name="+", on_delete=models.PROTECT))
