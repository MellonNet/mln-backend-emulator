from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from ..models.dynamic import Friendship, FriendshipStatus, Message, NetworkerFriendTrigger, get_or_none
from ..models.static import MLNError, MLNMessage, NetworkerFriendshipConditionDev

def _get_friendship(user, relation_id):
	try:
		friendship = Friendship.objects.get(id=relation_id)
	except ObjectDoesNotExist:
		raise RuntimeError("No friendship relation with ID %i exists" % relation_id)
	if friendship.from_user != user and friendship.to_user != user:
		raise RuntimeError("%s is not related to user %s" % (friendship, user))
	return friendship

def send_friend_invite(user, invitee_name):
	"""
	Send a friend request to someone.
	Raise RuntimeError if no user with the specified username exists.
	Raise RuntimeError if the user already is a friend or blocked friend.
	"""

	# Try to get the invitee
	invitee = get_or_none(User, username=invitee_name)
	if invitee is None:  # user doens't exist
		postman = get_or_none(User, username="Dead_Letter_Postman")
		if postman is not None:  # send the error through the Dead Letter Postman
			return user.messages.create(sender=postman, body_id=MLNError.MEMBER_NOT_FOUND)
		else:  # regular error
			raise RuntimeError("No user with the username %s exists" % invitee_name)

	# Try to get the current friendship status
	friendship = get_or_none(Friendship, from_user=user, to_user=invitee)
	if friendship is not None:  # already friends with this user
		if friendship.status == FriendshipStatus.PENDING: 
			error = MLNError.INVITATION_ALREADY_EXISTS
		elif friendship.status == FriendshipStatus.FRIEND: 
			error = MLNError.ALREADY_FRIENDS
		elif friendship.status == FriendshipStatus.BLOCKED: 
			error = MLNError.YOU_ARE_BLOCKED
		return user.messages.create(sender=invitee, body_id=error)

	# Send regular friend request to human users
	if not invitee.profile.is_networker: 
		return user.outgoing_friendships.create(to_user=invitee, status=FriendshipStatus.PENDING)

	# Handle networker friendship conditions
	for trigger in NetworkerFriendTrigger.objects.filter(networker=invitee):
		if not trigger.evaluate(user.inventory): continue
		if trigger.accept: user.outgoing_friendships.create(to_user=invitee, status=FriendshipStatus.FRIEND)
		trigger.send_message(user)
		break
	else:  # no trigger matched
		raise RuntimeError("No applicable friendship conditions for %s" % invitee)

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
		relation.from_user.messages.create(sender=user, body_id=MLNMessage.FRIEND_REQUEST_ACCEPT)
	else:
		relation.delete()
		relation.from_user.messages.create(sender=user, body_id=MLNMessage.FRIEND_REQUEST_REJECT)

def remove_friend(user, relation_id):
	"""
	Remove a friend from the user's friend list.
	Raise RuntimeError if
	- the friendship does not exist
	- the relation does not relate to this user
	"""
	relation = _get_friendship(user, relation_id)
	relation.delete()
	if relation.status != FriendshipStatus.BLOCKED:  # notify other user
		other = relation.from_user if relation.to_user == user else relation.to_user
		other.messages.create(sender=user, body_id=MLNMessage.FRIEND_REMOVE)

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
	relation.to_user.messages.create(sender=user, body_id=MLNMessage.FRIEND_BLOCK)
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
		return user.messages.create(sender=relation.from_user, body_id=MLNError.YOU_ARE_BLOCKED)
	relation.status = FriendshipStatus.FRIEND
	relation.to_user.messages.create(sender=user, body_id=MLNMessage.FRIEND_UNBLOCK)
	relation.save()

def are_friends(user, other_user_id):
	"""Return whether the users are friends."""
	return user.outgoing_friendships.filter(to_user_id=other_user_id, status=FriendshipStatus.FRIEND).exists() or user.incoming_friendships.filter(from_user_id=other_user_id, status=FriendshipStatus.FRIEND).exists()
