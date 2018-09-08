from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from ..models.dynamic import Friendship, FriendshipStatus
from ..models.static import MLNError

def _get_friendship(user, relation_id):
	try:
		friendship = Friendship.objects.get(id=relation_id)
	except ObjectDoesNotExist:
		raise RuntimeError("No friendship relation with ID %i exists" % relation_id)
	if friendship.from_profile != user.profile and friendship.to_profile != user.profile:
		raise RuntimeError("%s is not related to user %s" % (friendship, user))
	return friendship

def send_friend_invite(user, invitee_name):
	"""
	Send a friend request to someone.
	Raise RuntimeError if no user with the specified username exists.
	Raise RuntimeError if the user already is a friend or blocked friend.
	"""
	try:
		invitee = User.objects.get(username=invitee_name)
	except ObjectDoesNotExist:
		raise RuntimeError("No user with the username %s exists" % invitee_name)
	try:
		friendship = user.profile.outgoing_friendships.get(to_profile=invitee.profile)
		if friendship.status == FriendshipStatus.PENDING.value:
			return
		raise RuntimeError("Friendship to user %s already exists" % invitee_name)
	except ObjectDoesNotExist:
		pass
	user.profile.outgoing_friendships.create(to_profile=invitee.profile)

def handle_friend_invite_response(user, relation_id, accept):
	"""
	Accept or decline a friend request.
	Raise RuntimeError if
	- the friendship does not exist
	- the relation does not relate to this user, or
	- the relation is not a pending relation.
	"""
	relation = _get_friendship(user, relation_id)
	if relation.to_profile != user.profile:
		raise RuntimeError("%s is not related to this user" % relation)
	if relation.status != FriendshipStatus.PENDING.value:
		raise RuntimeError("%s is not a pending relation" % relation)
	if accept:
		relation.status = FriendshipStatus.FRIEND.value
		relation.save()
	else:
		relation.delete()

def remove_friend(user, relation_id):
	"""
	Remove a friend from the user's friend list.
	Raise RuntimeError if
	- the friendship does not exist
	- the relation does not relate to this user, or
	- the relation is not a friend relation.
	"""
	relation = _get_friendship(user, relation_id)
	if relation.status != FriendshipStatus.FRIEND.value:
		raise RuntimeError("%s is not a friend relation" % relation)
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
	if relation.status != FriendshipStatus.FRIEND.value:
		raise RuntimeError("%s is not a friend relation" % relation)
	# the direction of the relation is important for blocked friends
	if relation.to_profile == user.profile:
		friend = relation.from_profile
		relation.from_profile = user.profile
		relation.to_profile = friend
	relation.status = FriendshipStatus.BLOCKED.value
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
	if relation.status != FriendshipStatus.BLOCKED.value:
		raise RuntimeError("%s is not a blocked relation" % relation)
	if relation.from_profile != user.profile:
		raise MLNError(MLNError.YOU_ARE_BLOCKED)
	relation.status = FriendshipStatus.FRIEND.value
	relation.save()
