from ..utils import *
from ..items import *
from ..messages import *

class NetworkerFriendshipCondition(models.Model):
	"""Stores what a networker requires to accept a friend request, and the messages to be sent on success or failure."""
	networker = models.OneToOneField(User, related_name="friendship_condition", on_delete=models.CASCADE, limit_choices_to={"profile__is_networker": True})
	condition = models.ForeignKey(ItemInfo, related_name="+", blank=True, null=True, on_delete=models.SET_NULL, limit_choices_to=Q(type=ItemType.BADGE) | Q(type=ItemType.BLUEPRINT) | Q(type=ItemType.ITEM) | Q(type=ItemType.MASTERPIECE))
	success_body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)
	failure_body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)
