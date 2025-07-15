from ..utils import *

class FriendshipStatus(Enum):
	"""
	Statuses of a friendship relation.
	When a user requests another user to be their friend, the request is pending.
	Once the other user accepts, the status is changed to friend.
	If a user blocks a friend, the status is changed to blocked.
	"""
	FRIEND = auto()
	PENDING = auto()
	BLOCKED = auto()

class Friendship(models.Model):
	"""
	A friendship relation of two users.
	This is also used for friend requests and blocked friends.
	"""
	from_user = models.ForeignKey(User, related_name="outgoing_friendships", on_delete=models.CASCADE) # invite sender
	to_user = models.ForeignKey(User, related_name="incoming_friendships", on_delete=models.CASCADE) # invite recipient
	status = EnumField(FriendshipStatus)

	def __str__(self):
		return "%s -> %s: %s" % (self.from_user, self.to_user, self.get_status_display())
