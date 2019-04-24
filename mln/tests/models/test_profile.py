from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from mln.models.static import Answer, Color, ItemInfo, ItemType, Question
from mln.models.dynamic import AboutMe
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.models.test_static import item, starting_stack

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
	self.user.profile.save()

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
def page_skin(cls):
	cls.SKIN_ID = ItemInfo.objects.create(name="Skin Item", type=ItemType.SKIN).id

@setup
@requires(page_skin, one_user)
def has_skin(self):
	self.user.profile.add_inv_item(self.SKIN_ID)

@setup
@requires(item, one_user)
def user_has_item(self):
	self.user.inventory.create(item_id=self.ITEM_ID, qty=1)

@setup
@requires(item, two_users)
def other_user_has_item(self):
	self.other_user.profile.add_inv_item(self.ITEM_ID, 1)

class Profile(TestCase):
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

class ProfileSaveStatements(TestCase):
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

class ProfileSaveSkin_HasNoSkin(TestCase):
	SETUP = page_skin, one_user

	def test(self):
		self.user.profile.page_skin_id = self.SKIN_ID
		with self.assertRaises(ValidationError):
			self.user.profile.save()

class ProfileSaveSkin_WrongSkin(TestCase):
	SETUP = page_skin, user_has_item

	def test(self):
		self.user.profile.page_skin_id = self.ITEM_ID
		with self.assertRaises(ValidationError):
			self.user.profile.save()

class ProfileSaveSkin_HasSkin(TestCase):
	SETUP = has_skin,

	def test(self):
		self.user.profile.page_skin_id = self.SKIN_ID
		self.user.profile.save()
		self.assertEqual(self.user.profile.page_skin_id, self.SKIN_ID)

class ProfileInventory(TestCase):
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

class ProfileStartingStack(TestCase):
	SETUP = starting_stack, one_user

	def test(self):
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=10).exists())
