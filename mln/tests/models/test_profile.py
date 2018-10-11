from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from mln.models.static import Answer, Color, ItemInfo, ItemType, Question, StartingStack
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase

@cls_setup
def item(cls):
	cls.ITEM_ID = ItemInfo.objects.create(name="Test Item", type=ItemType.ITEM).id

@setup
def one_user(self):
	self.user = User.objects.create(username="user")

@setup
@requires(one_user)
def two_users(self):
	self.other_user = User.objects.create(username="other")

@setup
@requires(two_users)
def three_users(self):
	self.third_user = User.objects.create(username="third")

@setup
@requires(three_users)
def four_users(self):
	self.fourth_user = User.objects.create(username="fourth")

@setup
@requires(one_user)
def networker(self):
	self.user.profile.is_networker = True

@cls_setup
def statements(cls):
	cls.STATEMENTS = {}
	for i in range(10):
		question_id = Question.objects.create(text="Question %i" % i, mandatory=i == 0).id
		answers = []
		for j in range(10):
			answers.append(Answer.objects.create(text="Answer %i %i" % (i, j), question_id=question_id).id)
		cls.STATEMENTS[question_id] = answers

@cls_setup
def color(cls):
	cls.COLOR_ID = Color.objects.create(color=0).id

@cls_setup
def page_skin(cls):
	cls.SKIN_ID = ItemInfo.objects.create(name="Skin Item", type=ItemType.SKIN).id

@setup
@requires(page_skin, one_user)
def has_skin(self):
	self.user.profile.add_inv_item(self.SKIN_ID)

@cls_setup
@requires(item)
def starting_item(cls):
	StartingStack.objects.create(item_id=cls.ITEM_ID, qty=10)

@setup
@requires(item, one_user)
def user_has_item(self):
	self.user.profile.add_inv_item(self.ITEM_ID, 1)

@setup
@requires(item, two_users)
def other_user_has_item(self):
	self.other_user.profile.add_inv_item(self.ITEM_ID, 1)

class ProfileTest(TestCase):
	SETUP = one_user,

	def test_save_avatar_no_parts(self):
		self.user.profile.avatar = "test"
		with self.assertRaises(ValidationError):
			self.user.profile.save()

	def test_save_avatar_wrong_theme(self):
		self.user.profile.avatar = "1#3,6,22,20,29,1,3,5,2,3,2,2,1,1"
		with self.assertRaises(ValidationError):
			self.user.profile.save()

	def test_save_avatar_wrong_number_of_data(self):
		self.user.profile.avatar = "0#3,3,6,22,20,29,1,3,5,2,3,2,2,1,1"
		with self.assertRaises(ValidationError):
			self.user.profile.save()

	def test_save_avatar_ok(self):
		avatar = "0#3,6,22,20,29,1,3,5,2,3,2,2,1,1"
		self.user.profile.avatar = avatar
		self.user.profile.save()
		self.assertEqual(self.user.profile.avatar, avatar)

	def test_save_page_column_color_ok(self):
		self.user.profile.page_column_color_id = 0
		self.user.profile.save()
		self.assertEqual(self.user.profile.page_column_color_id, 0)

	def test_save_page_column_color_out_of_bounds(self):
		self.user.profile.page_column_color_id = 20
		with self.assertRaises(ValidationError):
			self.user.profile.save()

	def test_update_available_votes_update(self):
		before = self.user.profile.available_votes
		self.user.profile.available_votes = 0
		before_time = self.user.profile.last_vote_update_time - timedelta(days=1)
		self.user.profile.last_vote_update_time = before_time
		self.user.profile.update_available_votes()
		self.assertEqual(self.user.profile.available_votes, before)
		self.assertNotEqual(self.user.profile.last_vote_update_time, before_time)

	def test_update_available_votes_no_update(self):
		before_time = self.user.profile.last_vote_update_time
		self.user.profile.update_available_votes()
		self.assertEqual(self.user.profile.last_vote_update_time, before_time)

	def test_starting_item(self):
		self.assertFalse(self.user.inventory.exists())

class ProfileSaveStatementsTest(TestCase):
	SETUP = statements, one_user

	def test_wrong_answers(self):
		i = 0
		first_question_id = None
		for question_id, answers in self.STATEMENTS.items():
			if first_question_id is None:
				first_question_id = question_id
				continue
			setattr(self.user.profile, "statement_%i_question_id" % i, first_question_id)
			setattr(self.user.profile, "statement_%i_answer_id" % i, answers[0])
			i += 1
			if i == 6:
				break
		with self.assertRaises(ValidationError):
			self.user.profile.save()

	def test_duplicate_questions(self):
		question_id = next(iter(self.STATEMENTS))
		answer_id = self.STATEMENTS[question_id][0]
		for i in range(6):
			setattr(self.user.profile, "statement_%i_question_id" % i, question_id)
			setattr(self.user.profile, "statement_%i_answer_id" % i, answer_id)
		with self.assertRaises(ValidationError):
			self.user.profile.save()

	def test_mandatory_not_supplied(self):
		i = 0
		for question_id, answers in self.STATEMENTS.items():
			if question_id == 1:
				continue
			setattr(self.user.profile, "statement_%i_question_id" % i, question_id)
			setattr(self.user.profile, "statement_%i_answer_id" % i, answers[0])
			i += 1
			if i == 6:
				break
		with self.assertRaises(ValidationError):
			self.user.profile.save()

class ProfileSaveSkinHasNoSkinTest(TestCase):
	SETUP = page_skin, one_user

	def test_has_no_skin(self):
		self.user.profile.page_skin_id = self.SKIN_ID
		with self.assertRaises(ValidationError):
			self.user.profile.save()

class ProfileSaveSkinWrongSkinTest(TestCase):
	SETUP = page_skin, user_has_item

	def test_wrong_skin(self):
		self.user.profile.page_skin_id = self.ITEM_ID
		with self.assertRaises(ValidationError):
			self.user.profile.save()

class ProfileSaveSkinHasSkinTest(TestCase):
	SETUP = has_skin,

	def test_ok(self):
		self.user.profile.page_skin_id = self.SKIN_ID
		self.user.profile.save()
		self.assertEqual(self.user.profile.page_skin_id, self.SKIN_ID)

class ProfileInventoryTest(TestCase):
	SETUP = item, one_user

	def test_add_inv_item_empty(self):
		add_qty = 10
		self.user.profile.add_inv_item(self.ITEM_ID, add_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=add_qty).exists())

	def test_add_inv_item_exists(self):
		add_qty = 10
		self.user.profile.add_inv_item(self.ITEM_ID, add_qty)
		self.user.profile.add_inv_item(self.ITEM_ID, add_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=add_qty*2).exists())

	def test_remove_inv_item_exists(self):
		add_qty = 10
		remove_qty = 5
		self.user.profile.add_inv_item(self.ITEM_ID, add_qty)
		self.user.profile.remove_inv_item(self.ITEM_ID, remove_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=add_qty-remove_qty).exists())

	def test_remove_inv_item_delete_stack(self):
		add_qty = 10
		remove_qty = 10
		self.user.profile.add_inv_item(self.ITEM_ID, add_qty)
		self.user.profile.remove_inv_item(self.ITEM_ID, remove_qty)
		self.assertFalse(self.user.inventory.filter(item_id=self.ITEM_ID).exists())

	def test_remove_inv_item_no_stack(self):
		remove_qty = 10
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_inv_item(self.ITEM_ID, remove_qty)

	def test_remove_inv_item_not_enough_items(self):
		add_qty = 5
		remove_qty = 10
		self.user.profile.add_inv_item(self.ITEM_ID, add_qty)
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_inv_item(self.ITEM_ID, remove_qty)

class ProfileStartingItemTest(TestCase):
	SETUP = starting_item, one_user

	def test_starting_item(self):
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=10).exists())
