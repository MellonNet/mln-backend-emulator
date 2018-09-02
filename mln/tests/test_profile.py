from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from mln.models.dynamic import FriendshipStatus
from mln.models.static import ItemInfo, MLNError

class UserTest(TestCase):
	def setUp(self):
		self.user = User.objects.create()

class ProfileTest(UserTest):
	@classmethod
	def setUpTestData(cls):
		cls.APPLE = ItemInfo.objects.get(name="Apple").id
		cls.APPLE_PIE_BLUEPRINT = ItemInfo.objects.get(name="Apple Pie Blueprint").id

	def test_get_avatar_no_networker(self):
		self.assertEqual(self.user.profile.get_avatar(), self.user.profile.avatar)

	def test_get_avatar_networker(self):
		self.user.profile.is_networker = True
		self.assertEqual(self.user.profile.get_avatar(), self.user.profile.avatar+"#n")

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

	def test_send_friend_invite_no_user(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.send_friend_invite("missinguser")

	def test_handle_friend_invite_response_no_relation(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.handle_friend_invite_response(-1, True)

	def test_remove_friend_no_relation(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_friend(-1)

	def test_block_friend_no_relation(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.block_friend(-1)

	def test_unblock_friend_no_relation(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.unblock_friend(-1)

class TwoUsersTest(UserTest):
	def setUp(self):
		super().setUp()
		self.other_user = User.objects.create(username="other")

class NoFriendTest(TwoUsersTest):
	def test_send_friend_invite_ok(self):
		self.user.profile.send_friend_invite("other")
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).count(), 1)

	def test_send_friend_invite_again(self):
		self.user.profile.send_friend_invite("other")
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).count(), 1)
		self.user.profile.send_friend_invite("other")
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).count(), 1)

class FriendshipRelationTest(TwoUsersTest):
	def set_up_relation(self, status):
		self.friendship_id = self.user.profile.outgoing_friendships.create(to_profile=self.other_user.profile, status=status.value).id

class PendingFriendTest(FriendshipRelationTest):
	def setUp(self):
		super().setUp()
		self.set_up_relation(FriendshipStatus.PENDING)

	def test_handle_friend_invite_response_wrong_direction(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.handle_friend_invite_response(self.friendship_id, True)

	def test_handle_friend_invite_response_accept_ok(self):
		self.other_user.profile.handle_friend_invite_response(self.friendship_id, True)
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile, status=FriendshipStatus.FRIEND.value).count(), 1)

	def test_handle_friend_invite_response_decline_ok(self):
		self.other_user.profile.handle_friend_invite_response(self.friendship_id, False)
		self.assertFalse(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).exists())

	def test_remove_friend_pending(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_friend(self.friendship_id)

	def test_block_friend_pending(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.block_friend(self.friendship_id)

	def test_unblock_friend_pending(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.unblock_friend(self.friendship_id)

class FriendTest(FriendshipRelationTest):
	def setUp(self):
		super().setUp()
		self.set_up_relation(FriendshipStatus.FRIEND)

	def test_send_friend_invite_friend(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.send_friend_invite("other")

	def test_handle_friend_invite_response_friend(self):
		with self.assertRaises(RuntimeError):
			self.other_user.profile.handle_friend_invite_response(self.friendship_id, True)

	def test_remove_friend_ok(self):
		self.user.profile.remove_friend(self.friendship_id)
		self.assertFalse(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).exists())

	def test_block_friend_one_way_ok(self):
		self.user.profile.block_friend(self.friendship_id)
		self.assertFalse(self.other_user.profile.outgoing_friendships.filter(to_profile=self.user.profile).exists())
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile, status=FriendshipStatus.BLOCKED.value).count(), 1)

	def test_block_friend_other_way_ok(self):
		self.other_user.profile.block_friend(self.friendship_id)
		self.assertFalse(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).exists())
		self.assertEqual(self.other_user.profile.outgoing_friendships.filter(to_profile=self.user.profile, status=FriendshipStatus.BLOCKED.value).count(), 1)

	def test_unblock_friend_friend(self):
		with self.assertRaises(RuntimeError):
			self.other_user.profile.unblock_friend(self.friendship_id)

class BlockedFriendTest(FriendshipRelationTest):
	def setUp(self):
		super().setUp()
		self.set_up_relation(FriendshipStatus.BLOCKED)

	def test_send_friend_invite_blocked(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.send_friend_invite("other")

	def test_handle_friend_invite_response_blocked(self):
		with self.assertRaises(RuntimeError):
			self.other_user.profile.handle_friend_invite_response(self.friendship_id, True)

	def test_remove_friend_blocked(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_friend(self.friendship_id)

	def test_block_friend_blocked(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.block_friend(self.friendship_id)

	def test_unblock_friend_ok(self):
		self.user.profile.unblock_friend(self.friendship_id)
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile, status=FriendshipStatus.FRIEND.value).count(), 1)

	def test_unblock_friend_wrong_direction(self):
		with self.assertRaises(MLNError):
			self.other_user.profile.unblock_friend(self.friendship_id)

class ThirdFriendTest(FriendshipRelationTest):
	def setUp(self):
		super().setUp()
		self.set_up_relation(FriendshipStatus.FRIEND)
		self.third_user = User.objects.create(username="third")
		self.other_friendship_id = self.other_user.profile.outgoing_friendships.create(to_profile=self.third_user.profile, status=FriendshipStatus.FRIEND.value).id

	def test_handle_friend_invite_response_unrelated(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.handle_friend_invite_response(self.other_friendship_id, True)

	def test_remove_friend_unrelated(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.remove_friend(self.other_friendship_id)

	def test_block_friend_unrelated(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.block_friend(self.other_friendship_id)

	def test_unblock_friend_unrelated(self):
		with self.assertRaises(RuntimeError):
			self.user.profile.unblock_friend(self.other_friendship_id)
