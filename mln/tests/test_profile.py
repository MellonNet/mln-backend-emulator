from datetime import timedelta

from django.contrib.auth.models import User

from mln.models.static import ItemInfo, ItemType
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
@requires(one_user)
def networker(self):
	self.user.profile.is_networker = True

class ProfileTest(TestCase):
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
