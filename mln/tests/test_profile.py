from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from mln.models.static import ItemInfo

class UserTest(TestCase):
	def setUp(self):
		self.user = User.objects.create()

class TwoUsersTest(UserTest):
	def setUp(self):
		super().setUp()
		self.other_user = User.objects.create(username="other")

class ProfileTest(UserTest):
	@classmethod
	def setUpTestData(cls):
		cls.APPLE = ItemInfo.objects.get(name="Apple").id
		cls.APPLE_PIE_BLUEPRINT = ItemInfo.objects.get(name="Apple Pie Blueprint").id

	def test_add_inv_item_empty(self):
		add_qty = 10
		self.user.profile.add_inv_item(self.APPLE, add_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.APPLE, qty=add_qty).exists())

	def test_add_inv_item_exists(self):
		add_qty = 10
		self.user.profile.add_inv_item(self.APPLE, add_qty)
		self.user.profile.add_inv_item(self.APPLE, add_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.APPLE, qty=add_qty*2).exists())

	def test_remove_inv_item_exists(self):
		add_qty = 10
		remove_qty = 5
		self.user.profile.add_inv_item(self.APPLE, add_qty)
		self.user.profile.remove_inv_item(self.APPLE, remove_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.APPLE, qty=add_qty-remove_qty).exists())

	def test_remove_inv_item_delete_stack(self):
		add_qty = 10
		remove_qty = 10
		self.user.profile.add_inv_item(self.APPLE, add_qty)
		self.user.profile.remove_inv_item(self.APPLE, remove_qty)
		self.assertFalse(self.user.inventory.filter(item_id=self.APPLE).exists())

	def test_remove_inv_item_no_stack(self):
		remove_qty = 10
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_inv_item(self.APPLE, remove_qty)

	def test_remove_inv_item_not_enough_items(self):
		add_qty = 5
		remove_qty = 10
		self.user.profile.add_inv_item(self.APPLE, add_qty)
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_inv_item(self.APPLE, remove_qty)

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

	def test_use_blueprint_ok(self):
		blueprint = ItemInfo.objects.get(name="Apple Blueprint").id
		self.user.profile.use_blueprint(blueprint)
		self.assertTrue(self.user.inventory.filter(item_id=self.APPLE, qty=1).exists())

	def test_use_blueprint_not_a_blueprint(self):
		self.user.profile.add_inv_item(self.APPLE)
		with self.assertRaises(ValueError):
			self.user.profile.use_blueprint(self.APPLE)

	def test_use_blueprint_not_exists(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.use_blueprint(self.APPLE_PIE_BLUEPRINT)

	def test_use_blueprint_requirements_not_met(self):
		self.user.profile.add_inv_item(self.APPLE_PIE_BLUEPRINT)
		with self.assertRaises(RuntimeError):
			self.user.profile.use_blueprint(self.APPLE_PIE_BLUEPRINT)
