import random

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from ..models.dynamic import Friendship, FriendshipStatus, Profile, get_or_none
from ..models.static import MLNError, NetworkerFriendshipCondition

from .inventory import has_item

def _get_friendship(user, relation_id):
	try:
		friendship = Friendship.objects.get(id=relation_id)
	except ObjectDoesNotExist:
		raise RuntimeError("No friendship relation with ID %i exists" % relation_id)
	if friendship.from_user != user and friendship.to_user != user:
		raise RuntimeError("%s is not related to user %s" % (friendship, user))
	return friendship

def get_friend_request(from_user, to_user) -> Friendship | None:
	try:
		return from_user.outgoing_friendships.get(to_user=to_user)
	except ObjectDoesNotExist:
		return None

def get_friendship(user1, user2) -> Friendship | None:
	try:
		return user1.outgoing_friendships.get(to_user=user2)
	except ObjectDoesNotExist:
		try:
			return user2.outgoing_friendships.get(to_user=user1)
		except ObjectDoesNotExist:
			return None

def send_friend_invite(user, recipient_name):
	"""
	Send a friend request to someone.
	Raise RuntimeError if no user with the specified username exists.
	Raise RuntimeError if the user already is a friend or blocked friend.
	"""
	recipient = get_or_none(User, username=recipient_name)
	if recipient is None:
		raise RuntimeError("No user with the username %s exists" % recipient_name)

	friend_request = get_friend_request(from_user=user, to_user=recipient)
	if friend_request is not None:
		if friend_request.status == FriendshipStatus.PENDING:
			return
		else:
			raise RuntimeError("Friendship to user %s already exists" % recipient_name)

	recipient_profile = get_or_none(Profile, user=recipient)
	assert recipient_profile is not None  # all users have profiles
	if recipient_profile.is_networker:
		add_networker_friend(user, recipient)
	else:
		user.outgoing_friendships.create(to_user=recipient, status=FriendshipStatus.PENDING)

def add_networker_friend(user, networker):
	condition = get_or_none(NetworkerFriendshipCondition, networker=networker)
	if not condition: return  # all networkers must have a condition, no way to recover
	success = condition.condition_id is None or has_item(user, condition.condition_id)
	if success:
		user.outgoing_friendships.create(to_user=networker, status=FriendshipStatus.FRIEND)
		user.messages.create(sender=networker, body_id=condition.success_body_id)
	else:
		user.messages.create(sender=networker, body_id=condition.failure_body_id)

def handle_friend_invite_response(user, relation_id, accept):
	"""
	Accept or decline a friend request.
	Raise RuntimeError if
	- the friendship does not exist
	- the relation does not relate to this user, or
	- the relation is not a pending relation.
	"""
	relation = _get_friendship(user, relation_id)
	if relation.to_user != user:
		raise RuntimeError("%s is not related to this user" % relation)
	if relation.status != FriendshipStatus.PENDING:
		raise RuntimeError("%s is not a pending relation" % relation)
	if accept:
		relation.status = FriendshipStatus.FRIEND
		relation.save()
	else:
		relation.delete()

def remove_friend(user, relation_id):
	"""
	Remove a friend from the user's friend list.
	Raise RuntimeError if
	- the friendship does not exist, or
	- the relation does not relate to this user
	Raise MLNError if the the user is blocked.
	"""
	relation = _get_friendship(user, relation_id)
	if relation.status == FriendshipStatus.BLOCKED and relation.from_user != user:
		raise MLNError(MLNError.YOU_ARE_BLOCKED)
	relation.delete()

def block_friend(user, relation_id):
	"""
	Block a friend.
	Raise RuntimeError if
	- the friendship does not exist
	- the relation does not relate to this user, or
	- the relation is not a friend relation.
	"""
	relation = _get_friendship(user, relation_id)
	if relation.status != FriendshipStatus.FRIEND:
		raise RuntimeError("%s is not a friend relation" % relation)
	# the direction of the relation is important for blocked friends
	if relation.to_user == user:
		friend = relation.from_user
		relation.from_user = user
		relation.to_user = friend
	relation.status = FriendshipStatus.BLOCKED
	relation.save()

def unblock_friend(user, relation_id):
	"""
	Unblock a friend.
	Raise RuntimeError if
	- the friendship does not exist
	- the relation does not relate to this user, or
	- the relation is not a blocked relation.
	Raise MLNError if the user is the one who has been blocked instead of the blocker.
	"""
	relation = _get_friendship(user, relation_id)
	if relation.status != FriendshipStatus.BLOCKED:
		raise RuntimeError("%s is not a blocked relation" % relation)
	if relation.from_user != user:
		raise MLNError(MLNError.YOU_ARE_BLOCKED)
	relation.status = FriendshipStatus.FRIEND
	relation.save()

def are_friends(user, other_user_id):
	"""Return whether the users are friends."""
	return user.outgoing_friendships.filter(to_user_id=other_user_id, status=FriendshipStatus.FRIEND).exists() or user.incoming_friendships.filter(from_user_id=other_user_id, status=FriendshipStatus.FRIEND).exists()

def choose_friend(user, allow_networkers=False):
	"""Returns a random friend from the user's friend list."""
	# Wouldn't help to use Q objects because we wouldn't know which user is the friend
	incoming = user.incoming_friendships.filter(from_user__profile__is_networker=allow_networkers, status=FriendshipStatus.FRIEND)
	outgoing = user.outgoing_friendships.filter(to_user__profile__is_networker=allow_networkers, status=FriendshipStatus.FRIEND)
	incoming_friends = [friendship.from_user for friendship in incoming]
	outgoing_friends = [friendship.to_user for friendship in outgoing]
	friends = incoming_friends + outgoing_friends
	if friends: return random.choice(friends)
