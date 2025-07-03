from django.contrib.auth.models import User

from mln.models.dynamic import FriendshipStatus
from mln.models.static import MLNError
from mln.services.friend import block_friend, handle_friend_invite_response, remove_friend, send_friend_invite, unblock_friend
from mln.tests.setup_testcase import requires, setup, TestCase
from mln.tests.models.test_profile import four_users, one_user, three_users, two_users

@setup
@requires(two_users)
def pending_friends(self):
	self.friendship_id = self.user.outgoing_friendships.create(to_user=self.other_user, status=FriendshipStatus.PENDING).id

@setup
@requires(two_users)
def pending_friends_other_way(self):
	self.other_user.outgoing_friendships.create(to_user=self.user, status=FriendshipStatus.PENDING)

@setup
@requires(two_users)
def friends(self):
	self.friendship_id = self.user.outgoing_friendships.create(to_user=self.other_user, status=FriendshipStatus.FRIEND).id

@setup
@requires(two_users)
def blocked_friends(self):
	self.friendship_id = self.user.outgoing_friendships.create(to_user=self.other_user, status=FriendshipStatus.BLOCKED).id

@setup
@requires(friends, three_users)
def friend_of_friend(self):
	self.other_friendship_id = self.other_user.outgoing_friendships.create(to_user=self.third_user, status=FriendshipStatus.FRIEND).id

@setup
@requires(friends, three_users)
def two_friends(self):
	self.user.outgoing_friendships.create(to_user=self.third_user, status=FriendshipStatus.FRIEND).id

@setup
@requires(two_friends, four_users)
def three_friends(self):
	self.user.outgoing_friendships.create(to_user=self.fourth_user, status=FriendshipStatus.FRIEND).id

class OneUser(TestCase):
	SETUP = one_user,

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

class NoFriend(TestCase):
	SETUP = two_users,

	def test_send_friend_invite_ok(self):
		send_friend_invite(self.user, "other")
		self.assertEqual(self.user.outgoing_friendships.filter(to_user=self.other_user).count(), 1)

	def test_send_friend_invite_again(self):
		send_friend_invite(self.user, "other")
		self.assertEqual(self.user.outgoing_friendships.filter(to_user=self.other_user).count(), 1)
		send_friend_invite(self.user, "other")
		self.assertEqual(self.user.outgoing_friendships.filter(to_user=self.other_user).count(), 1)

class PendingFriend(TestCase):
	SETUP = pending_friends,

	def test_handle_friend_invite_response_wrong_direction(self):
		with self.assertRaises(RuntimeError):
			handle_friend_invite_response(self.user, self.friendship_id, True)

	def test_handle_friend_invite_response_accept_ok(self):
		handle_friend_invite_response(self.other_user, self.friendship_id, True)
		self.assertEqual(self.user.outgoing_friendships.filter(to_user=self.other_user, status=FriendshipStatus.FRIEND).count(), 1)

	def test_handle_friend_invite_response_decline_ok(self):
		handle_friend_invite_response(self.other_user, self.friendship_id, False)
		self.assertFalse(self.user.outgoing_friendships.filter(to_user=self.other_user).exists())

	def test_block_friend_pending(self):
		with self.assertRaises(RuntimeError):
			block_friend(self.user, self.friendship_id)

	def test_unblock_friend_pending(self):
		with self.assertRaises(RuntimeError):
			unblock_friend(self.user, self.friendship_id)

class Friend(TestCase):
	SETUP = friends,

	def test_send_friend_invite_friend(self):
		with self.assertRaises(RuntimeError):
			send_friend_invite(self.user, "other")

	def test_handle_friend_invite_response_friend(self):
		with self.assertRaises(RuntimeError):
			handle_friend_invite_response(self.other_user, self.friendship_id, True)

	def test_remove_friend_ok(self):
		remove_friend(self.user, self.friendship_id)
		self.assertFalse(self.user.outgoing_friendships.filter(to_user=self.other_user).exists())

	def test_block_friend_one_way_ok(self):
		block_friend(self.user, self.friendship_id)
		self.assertFalse(self.other_user.outgoing_friendships.filter(to_user=self.user).exists())
		self.assertEqual(self.user.outgoing_friendships.filter(to_user=self.other_user, status=FriendshipStatus.BLOCKED).count(), 1)

	def test_block_friend_other_way_ok(self):
		block_friend(self.other_user, self.friendship_id)
		self.assertFalse(self.user.outgoing_friendships.filter(to_user=self.other_user).exists())
		self.assertEqual(self.other_user.outgoing_friendships.filter(to_user=self.user, status=FriendshipStatus.BLOCKED).count(), 1)

	def test_unblock_friend_friend(self):
		with self.assertRaises(RuntimeError):
			unblock_friend(self.other_user, self.friendship_id)

class BlockedFriend(TestCase):
	SETUP = blocked_friends,

	def test_send_friend_invite_blocked(self):
		with self.assertRaises(RuntimeError):
			send_friend_invite(self.user, "other")

	def test_handle_friend_invite_response_blocked(self):
		with self.assertRaises(RuntimeError):
			handle_friend_invite_response(self.other_user, self.friendship_id, True)

	def test_remove_friend_ok(self):
		remove_friend(self.user, self.friendship_id)
		self.assertEqual(self.user.outgoing_friendships.count(), 0)
		self.assertEqual(self.user.incoming_friendships.count(), 0)

	def test_remove_friend_wrong_direction(self):
		with self.assertRaises(MLNError):
			remove_friend(self.other_user, self.friendship_id)

	def test_block_friend_blocked(self):
		with self.assertRaises(RuntimeError):
			block_friend(self.user, self.friendship_id)

	def test_unblock_friend_ok(self):
		unblock_friend(self.user, self.friendship_id)
		self.assertEqual(self.user.outgoing_friendships.filter(to_user=self.other_user, status=FriendshipStatus.FRIEND).count(), 1)

	def test_unblock_friend_wrong_direction(self):
		with self.assertRaises(MLNError):
			unblock_friend(self.other_user, self.friendship_id)

class ThirdFriend(TestCase):
	SETUP = friend_of_friend,

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
