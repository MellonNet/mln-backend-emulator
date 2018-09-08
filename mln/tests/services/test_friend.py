from django.contrib.auth.models import User

from mln.models.dynamic import FriendshipStatus
from mln.models.static import MLNError
from mln.services.friend import block_friend, handle_friend_invite_response, remove_friend, send_friend_invite, unblock_friend
from mln.tests.test_profile import UserTest, TwoUsersTest

class OneUserTest(UserTest):
	def test_send_friend_invite_no_user(self):
		with self.assertRaises(RuntimeError):
			send_friend_invite(self.user, "missinguser")

	def test_handle_friend_invite_response_no_relation(self):
		with self.assertRaises(RuntimeError):
			handle_friend_invite_response(self.user, -1, True)

	def test_remove_friend_no_relation(self):
		with self.assertRaises(RuntimeError):
			remove_friend(self.user, -1)

	def test_block_friend_no_relation(self):
		with self.assertRaises(RuntimeError):
			block_friend(self.user, -1)

	def test_unblock_friend_no_relation(self):
		with self.assertRaises(RuntimeError):
			unblock_friend(self.user, -1)

class NoFriendTest(TwoUsersTest):
	def test_send_friend_invite_ok(self):
		send_friend_invite(self.user, "other")
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).count(), 1)

	def test_send_friend_invite_again(self):
		send_friend_invite(self.user, "other")
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).count(), 1)
		send_friend_invite(self.user, "other")
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
			handle_friend_invite_response(self.user, self.friendship_id, True)

	def test_handle_friend_invite_response_accept_ok(self):
		handle_friend_invite_response(self.other_user, self.friendship_id, True)
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile, status=FriendshipStatus.FRIEND.value).count(), 1)

	def test_handle_friend_invite_response_decline_ok(self):
		handle_friend_invite_response(self.other_user, self.friendship_id, False)
		self.assertFalse(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).exists())

	def test_remove_friend_pending(self):
		with self.assertRaises(RuntimeError):
			remove_friend(self.user, self.friendship_id)

	def test_block_friend_pending(self):
		with self.assertRaises(RuntimeError):
			block_friend(self.user, self.friendship_id)

	def test_unblock_friend_pending(self):
		with self.assertRaises(RuntimeError):
			unblock_friend(self.user, self.friendship_id)

class FriendTest(FriendshipRelationTest):
	def setUp(self):
		super().setUp()
		self.set_up_relation(FriendshipStatus.FRIEND)

	def test_send_friend_invite_friend(self):
		with self.assertRaises(RuntimeError):
			send_friend_invite(self.user, "other")

	def test_handle_friend_invite_response_friend(self):
		with self.assertRaises(RuntimeError):
			handle_friend_invite_response(self.other_user, self.friendship_id, True)

	def test_remove_friend_ok(self):
		remove_friend(self.user, self.friendship_id)
		self.assertFalse(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).exists())

	def test_block_friend_one_way_ok(self):
		block_friend(self.user, self.friendship_id)
		self.assertFalse(self.other_user.profile.outgoing_friendships.filter(to_profile=self.user.profile).exists())
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile, status=FriendshipStatus.BLOCKED.value).count(), 1)

	def test_block_friend_other_way_ok(self):
		block_friend(self.other_user, self.friendship_id)
		self.assertFalse(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile).exists())
		self.assertEqual(self.other_user.profile.outgoing_friendships.filter(to_profile=self.user.profile, status=FriendshipStatus.BLOCKED.value).count(), 1)

	def test_unblock_friend_friend(self):
		with self.assertRaises(RuntimeError):
			unblock_friend(self.other_user, self.friendship_id)

class BlockedFriendTest(FriendshipRelationTest):
	def setUp(self):
		super().setUp()
		self.set_up_relation(FriendshipStatus.BLOCKED)

	def test_send_friend_invite_blocked(self):
		with self.assertRaises(RuntimeError):
			send_friend_invite(self.user, "other")

	def test_handle_friend_invite_response_blocked(self):
		with self.assertRaises(RuntimeError):
			handle_friend_invite_response(self.other_user, self.friendship_id, True)

	def test_remove_friend_blocked(self):
		with self.assertRaises(RuntimeError):
			remove_friend(self.user, self.friendship_id)

	def test_block_friend_blocked(self):
		with self.assertRaises(RuntimeError):
			block_friend(self.user, self.friendship_id)

	def test_unblock_friend_ok(self):
		unblock_friend(self.user, self.friendship_id)
		self.assertEqual(self.user.profile.outgoing_friendships.filter(to_profile=self.other_user.profile, status=FriendshipStatus.FRIEND.value).count(), 1)

	def test_unblock_friend_wrong_direction(self):
		with self.assertRaises(MLNError):
			unblock_friend(self.other_user, self.friendship_id)

class ThirdFriendTest(FriendshipRelationTest):
	def setUp(self):
		super().setUp()
		self.set_up_relation(FriendshipStatus.FRIEND)
		self.third_user = User.objects.create(username="third")
		self.other_friendship_id = self.other_user.profile.outgoing_friendships.create(to_profile=self.third_user.profile, status=FriendshipStatus.FRIEND.value).id

	def test_handle_friend_invite_response_unrelated(self):
		with self.assertRaises(RuntimeError):
			handle_friend_invite_response(self.user, self.other_friendship_id, True)

	def test_remove_friend_unrelated(self):
		with self.assertRaises(RuntimeError):
			remove_friend(self.user, self.other_friendship_id)

	def test_block_friend_unrelated(self):
		with self.assertRaises(RuntimeError):
			block_friend(self.user, self.other_friendship_id)

	def test_unblock_friend_unrelated(self):
		with self.assertRaises(RuntimeError):
			unblock_friend(self.user, self.other_friendship_id)
