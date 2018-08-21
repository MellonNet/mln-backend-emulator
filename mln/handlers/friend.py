"""Friend functionality handlers."""
from django.contrib.auth.models import User

from ..models.dynamic import Friendship, FriendshipStatus
from ..models.static import MLNError

def handle_friend_process_blocking(user, request):
	"""Block or unblock a friend."""
	relation_id = int(request.get("friendRelationID"))
	block = request.get("block") == "true"
	relation = Friendship.objects.get(id=relation_id)
	if block:
		# the direction of the relation is important for blocked friends
		if relation.to_profile.user == user:
			friend = relation.from_profile
			relation.from_profile = user.profile
			relation.to_profile = friend
		relation.status = FriendshipStatus.BLOCKED.value
	else:
		if relation.from_profile.user == user:
			relation.status = FriendshipStatus.FRIEND.value
		else:
			raise MLNError(MLNError.YOU_ARE_BLOCKED)
	relation.save()

def handle_friend_process_invitation(user, request):
	"""Accept or decline a friend request."""
	relation_id = int(request.get("friendRelationID"))
	accept = request.get("accept") == "true"
	relation = Friendship.objects.get(id=relation_id)
	if accept:
		relation.status = FriendshipStatus.FRIEND.value
		relation.save()
	else:
		relation.delete()

def handle_friend_remove_member(user, request):
	"""Delete a friend from the user's friend list."""
	relation_id = int(request.get("friendRelationID"))
	Friendship.objects.get(id=relation_id).delete()

def handle_friend_send_invitation(user, request):
	"""Send a friend request to someone."""
	invitee_name = request.get("inviteeName")
	invitee = User.objects.get(username=invitee_name)
	friendship = Friendship.objects.create(from_profile=user.profile, to_profile=invitee.profile)
