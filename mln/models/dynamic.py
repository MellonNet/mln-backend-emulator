"""
Models for objects that will be created, modified and deleted during runtime.
These include user profiles, inventory stacks and messages.
Since modules have a lot of models associated with them, their models are in dedicated files.
"""
import datetime
from enum import auto, Enum

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now

from .static import Answer, BlueprintInfo, BlueprintRequirement, Color, EnumField, ItemInfo, ItemType, MessageBody, MLNError, Stack, Question

DAY = datetime.timedelta(days=1)

class Message(models.Model):
	"""
	A message sent from one user to another.
	User messages can only be sent to friends, while messages sent by networkers don't have this restriction.
	Message contents are determined by a prefabricated message text that can be chosen.
	In the case of replies, the original message is also stored, so that the subject can be displayed as RE: <original>.
	Messages can have attachments.
	"""
	sender = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
	recipient = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
	body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)
	reply_body = models.ForeignKey(MessageBody, null=True, blank=True, related_name="+", on_delete=models.CASCADE)
	is_read = models.BooleanField(default=False)

	def __str__(self):
		if self.reply_body_id is not None:
			subject = "RE: "+self.reply_body.subject
		else:
			subject = self.body.subject
		return "Message from %s to %s, subject \"%s\", is read: %s" % (self.sender, self.recipient, subject, self.is_read)

class Attachment(Stack):
	"""An Attachment, a stack sent with a message."""
	message = models.ForeignKey(Message, related_name="attachments", on_delete=models.CASCADE)

	def __str__(self):
		return "%s attached to %s" % (super().__str__(), self.message)

class Profile(models.Model):
	"""
	MLN-specific user data.
	This includes the avatar, user rank, available votes, page skin and page colors, as well as "About me" statements.
	"""
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	is_networker = models.BooleanField(default=False)
	avatar = models.CharField(max_length=64, default="0#1,6,1,16,5,1,6,13,2,9,2,2,1,1")
	rank = models.PositiveSmallIntegerField(default=0)
	available_votes = models.PositiveSmallIntegerField(default=20)
	last_vote_update_time = models.DateTimeField(default=now)
	page_skin = models.ForeignKey(ItemInfo, null=True, blank=True, related_name="+", on_delete=models.PROTECT, limit_choices_to={"type": ItemType.SKIN.value})
	page_color = models.ForeignKey(Color, null=True, blank=True, related_name="+", on_delete=models.CASCADE)
	page_column_color_id = models.PositiveSmallIntegerField(null=True, blank=True) # hardcoded for some reason
	friends = models.ManyToManyField("self", through="Friendship", symmetrical=False)

	def __str__(self):
		return self.user.username

	def add_inv_item(self, item_id, qty=1):
		"""
		Add one or more items to the user's inventory.
		Always use this function instead of creating InventoryStacks directly.
		This function creates a stack only if it does not already exist, and otherwise adds to the existing stack.
		"""
		try:
			stack = self.user.inventory.get(item_id=item_id)
			stack.qty += qty
			stack.save()
			return stack
		except ObjectDoesNotExist:
			return InventoryStack.objects.create(item_id=item_id, qty=qty, owner=self.user)

	def remove_inv_item(self, item_id, qty=1):
		"""
		Remove one or more items from the user's inventory.
		Always use this function instead of modifying InventoryStacks directly.
		This function subtracts the number of items from the stack, and deletes the stack if no more items are left.
		Raise RuntimeError if the stack to remove items from does not exist, or if it has fewer items than should be removed.
		"""
		try:
			stack = self.user.inventory.get(item_id=item_id)
		except ObjectDoesNotExist:
			raise RuntimeError("No stack of item ID %i of user %s exists to delete from" % (item_id, self))
		if stack.qty > qty:
			stack.qty -= qty
			stack.save()
		elif stack.qty == qty:
			stack.delete()
		else:
			raise RuntimeError("%s has fewer items than the %i requested to delete" % (stack, qty))

	def update_available_votes(self):
		"""
		Calculate how many votes are available.
		Votes regenerate at a rate determined by rank, but will only be updated if you explicitly call this function.
		"""
		time_since_last_update = now() - self.last_vote_update_time
		max_votes = 20 + 8 * self.rank
		new_votes, time_remainder = divmod(time_since_last_update, (DAY / max_votes))
		if new_votes > 0:
			self.available_votes = min(self.available_votes + new_votes, max_votes)
			self.last_vote_update_time = now() - time_remainder
			self.save()

	def use_blueprint(self, blueprint_id):
		"""
		Use a blueprint to create a new item and add it to the user's inventory.
		Remove the blueprint's requirements from the user's inventory.
		Raise ValueError if the passed ID does not belong to a blueprint.
		Raise RuntimeError if the blueprint or a required item is not in the user's inventory.
		"""
		if not self.user.inventory.filter(item_id=blueprint_id).exists():
			raise RuntimeError("Blueprint not in inventory")
		try:
			blueprint_info = BlueprintInfo.objects.get(item_id=blueprint_id)
		except ObjectDoesNotExist:
			raise ValueError("Item with ID %i is not a blueprint" % blueprint_id)
		requirements = BlueprintRequirement.objects.filter(blueprint_item_id=blueprint_id)
		# verify that requirements are met
		for requirement in requirements:
			if not self.user.inventory.filter(item_id=requirement.item_id, qty__gte=requirement.qty).exists():
				raise RuntimeError("Blueprint requirements not met")
		# remove required items
		for requirement in requirements:
			self.remove_inv_item(requirement.item_id, requirement.qty)
		# add newly built item
		self.add_inv_item(blueprint_info.build_id)

	def _get_friendship(self, relation_id):
		try:
			friendship = Friendship.objects.get(id=relation_id)
		except ObjectDoesNotExist:
			raise RuntimeError("No friendship relation with ID %i exists" % relation_id)
		if friendship.from_profile != self and friendship.to_profile != self:
			raise RuntimeError("%s is not related to user %s" % (friendship, self))
		return friendship

	def send_friend_invite(self, invitee_name):
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
			friendship = self.outgoing_friendships.get(to_profile=invitee.profile)
			if friendship.status == FriendshipStatus.PENDING.value:
				return
			raise RuntimeError("Friendship to user %s already exists" % invitee_name)
		except ObjectDoesNotExist:
			pass
		self.outgoing_friendships.create(to_profile=invitee.profile)

	def handle_friend_invite_response(self, relation_id, accept):
		"""
		Accept or decline a friend request.
		Raise RuntimeError if
		- the friendship does not exist
		- the relation does not relate to this user, or
		- the relation is not a pending relation.
		"""
		relation = self._get_friendship(relation_id)
		if relation.to_profile != self:
			raise RuntimeError("%s is not related to this user" % relation)
		if relation.status != FriendshipStatus.PENDING.value:
			raise RuntimeError("%s is not a pending relation" % relation)
		if accept:
			relation.status = FriendshipStatus.FRIEND.value
			relation.save()
		else:
			relation.delete()

	def remove_friend(self, relation_id):
		"""
		Remove a friend from the user's friend list.
		Raise RuntimeError if
		- the friendship does not exist
		- the relation does not relate to this user, or
		- the relation is not a friend relation.
		"""
		relation = self._get_friendship(relation_id)
		if relation.status != FriendshipStatus.FRIEND.value:
			raise RuntimeError("%s is not a friend relation" % relation)
		relation.delete()

	def block_friend(self, relation_id):
		"""
		Block a friend.
		Raise RuntimeError if
		- the friendship does not exist
		- the relation does not relate to this user, or
		- the relation is not a friend relation.
		"""
		relation = self._get_friendship(relation_id)
		if relation.status != FriendshipStatus.FRIEND.value:
			raise RuntimeError("%s is not a friend relation" % relation)
		# the direction of the relation is important for blocked friends
		if relation.to_profile == self:
			friend = relation.from_profile
			relation.from_profile = self
			relation.to_profile = friend
		relation.status = FriendshipStatus.BLOCKED.value
		relation.save()

	def unblock_friend(self, relation_id):
		"""
		Unblock a friend.
		Raise RuntimeError if
		- the friendship does not exist
		- the relation does not relate to this user, or
		- the relation is not a blocked relation.
		Raise MLNError if the user is the one who has been blocked instead of the blocker.
		"""
		relation = self._get_friendship(relation_id)
		if relation.status != FriendshipStatus.BLOCKED.value:
			raise RuntimeError("%s is not a blocked relation" % relation)
		if relation.from_profile != self:
			raise MLNError(MLNError.YOU_ARE_BLOCKED)
		relation.status = FriendshipStatus.FRIEND.value
		relation.save()

for i in range(6):
	Profile.add_to_class("statement_%i_question" % i, models.ForeignKey(Question, null=True, blank=True, related_name="+", on_delete=models.PROTECT))
	Profile.add_to_class("statement_%i_answer" % i, models.ForeignKey(Answer, null=True, blank=True, related_name="+", on_delete=models.PROTECT))

class InventoryStack(Stack):
	"""A stack of items in the user's inventory."""
	owner = models.ForeignKey(User, related_name="inventory", on_delete=models.CASCADE)

	def __str__(self):
		return "%s's stack of %s" % (self.owner, super().__str__())

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
	from_profile = models.ForeignKey(Profile, related_name="outgoing_friendships", on_delete=models.CASCADE) # invite sender
	to_profile = models.ForeignKey(Profile, related_name="incoming_friendships", on_delete=models.CASCADE) # invite recipient
	status = EnumField(FriendshipStatus, default=FriendshipStatus.PENDING.value)

	def __str__(self):
		return "%s -> %s: %s" % (self.from_profile.user, self.to_profile.user, self.get_status_display())

def get_or_none(cls, *args, **kwargs):
	"""Get a model instance according to the filters, or return None if no matching model instance was found."""
	try:
		return cls.objects.get(*args, **kwargs)
	except ObjectDoesNotExist:
		return None
