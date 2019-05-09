from django.core.exceptions import ValidationError

from mln.models.dynamic import AboutMe
from mln.models.static import Answer, Question
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.models.dupe_testcase import DupeTest
from mln.tests.models.test_profile import one_user, two_users, user_has_item
from mln.tests.models.test_static import body, item

@setup
@requires(body, two_users)
def message(self):
	self.message = self.user.messages.create(sender=self.other_user, body_id=self.BODY.id)

@setup
@requires(item, message)
def attachment(self):
	self.message.attachments.create(item_id=self.ITEM_ID, qty=1)

@cls_setup
def statements(cls):
	cls.STATEMENTS = {}
	for i in range(10):
		question_id = Question.objects.create(text="Question %i" % i, mandatory=i == 0).id
		answers = []
		for j in range(10):
			answers.append(Answer.objects.create(text="Answer %i %i" % (i, j), question_id=question_id).id)
		cls.STATEMENTS[question_id] = answers

class DuplicateAttachment(DupeTest):
	SETUP = attachment,

class DuplicateInventoryStack(DupeTest):
	SETUP = user_has_item,

class AboutMeTest(TestCase):
	SETUP = statements, one_user

	def test_wrong_answers(self):
		about_me = AboutMe(user=self.user)
		i = 0
		first_question_id = None
		for question_id, answers in self.STATEMENTS.items():
			if first_question_id is None:
				first_question_id = question_id
				continue
			setattr(about_me, "question_%i_id" % i, first_question_id)
			setattr(about_me, "answer_%i_id" % i, answers[0])
			i += 1
			if i == 6:
				break
		with self.assertRaises(ValidationError):
			about_me.save()

	def test_duplicate_questions(self):
		about_me = AboutMe(user=self.user)
		question_id = next(iter(self.STATEMENTS))
		answer_id = self.STATEMENTS[question_id][0]
		for i in range(6):
			setattr(about_me, "question_%i_id" % i, question_id)
			setattr(about_me, "answer_%i_id" % i, answer_id)
		with self.assertRaises(ValidationError):
			about_me.save()

	def test_mandatory_not_supplied(self):
		about_me = AboutMe(user=self.user)
		i = 0
		for question_id, answers in self.STATEMENTS.items():
			if question_id == 1:
				continue
			setattr(about_me, "question_%i_id" % i, question_id)
			setattr(about_me, "answer_%i_id" % i, answers[0])
			i += 1
			if i == 6:
				break
		with self.assertRaises(ValidationError):
			about_me.save()
