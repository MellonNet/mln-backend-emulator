"""
Read-only models used to describe general MLN concepts and data that won't change (except in the case of an update of MLN itself), not dynamic data like users.
These include items and associated info, "about me" questions & answers and message texts.
"""
from enum import auto, Enum

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

class MLNMessage:
	"""
	These are messages that can be sent to the user on certain conditions.
	They don't necessarily indicate an error within MLN, rather inform the user they need to do something different.
	Like MLNError, these IDs refer to instances of MessageBody.
	"""
	I_DONT_GET_IT = 46222

# can't change this without also changing the xml - error descriptions are clientside
class MLNError(Exception):
	"""
	An error with an error message that will be shown to the user.
	The displayed messages are actually mail messages in a hidden category.
	As such, this list of raw IDs is not completely ideal and will break when message IDs are reassigned.
	"""
	OPERATION_FAILED = 46304
	YOU_ARE_BLOCKED = 46305
	ALREADY_FRIENDS = 46307
	INVITATION_ALREADY_EXISTS = 46308
	ITEM_MISSING = 46309
	ITEM_IS_NOT_MAILABLE = 46310
	MODULE_ALREADY_SETUP = 46311
	MODULE_IS_NOT_READY = 46312
	OUT_OF_VOTES = 46313
	MLN_OFFLINE = 47570
	MEMBER_NOT_FOUND = 52256

	def __init__(self, id):
		super().__init__()
		self.id = id

class ItemType(Enum):
	"""Types of items. The main use is to place items into different inventory tabs."""
	BACKGROUND = auto()
	BADGE = auto()
	BLUEPRINT = auto()
	ITEM = auto()
	LOOP = auto()
	MASTERPIECE = auto()
	MODULE = auto()
	MOVIE = auto()
	SKIN = auto()
	STICKER = auto()

class EnumField(models.PositiveSmallIntegerField):
	def __init__(self, enum, *args, **kwargs):
		self.enum = enum
		super().__init__(*args, choices=[(member, member.name.lower().replace("_", " ")) for member in enum], **kwargs)

	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		args = self.enum, *args
		del kwargs["choices"]
		return name, path, args, kwargs

	def from_db_value(self, value, expression, connection):
		if value is None:
			return None
		return self.enum(value)

	def get_prep_value(self, value):
		if value is None:
			return None
		if isinstance(value, str):
			return self.enum[value[value.index(".")+1:]].value
		return value.value

	def to_python(self, value):
		if value is None:
			return None
		if isinstance(value, str):
			return self.enum[value[value.index(".")+1:]]
		return value

class ItemInfo(models.Model):
	"""
	An item.
	This is not the class for the inventory contents of users, for that, see InventoryStack.
	Instead, this describes abstract items that exist in MLN.
	In MLN, almost everything you can possess is an item, including (abstract) modules, loops, stickers, page skins and more. See ItemType for a complete list.
	"""
	name = models.CharField(max_length=64)
	type = EnumField(ItemType)

	class Meta:
		ordering = ("name",)
		constraints = (models.UniqueConstraint(fields=("name", "type"), name="item_info_unique_name_type"),)

	def __str__(self):
		return self.name

class Stack(models.Model):
	"""
	Multiple instances of an item.
	This abstract class is used as a base for more specific stacks with a certain purpose, like inventory stacks or attachments.
	"""
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE)
	qty = models.PositiveSmallIntegerField()

	class Meta:
		abstract = True

	def __str__(self):
		return "%ix %s (%s)" % (self.qty, self.item.name, self.item.get_type_display())

class BlueprintInfo(models.Model):
	"""Stores which item the blueprint produces."""
	item = models.OneToOneField(ItemInfo, related_name="+", on_delete=models.CASCADE)
	build = models.OneToOneField(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.BADGE) | Q(type=ItemType.ITEM) | Q(type=ItemType.MASTERPIECE) | Q(type=ItemType.MODULE) | Q(type=ItemType.MOVIE) | Q(type=ItemType.SKIN))

	def __str__(self):
		return str(self.item)

class BlueprintRequirement(Stack):
	"""Stores how many of an item a blueprint needs to produce an item."""
	blueprint_item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE)
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.BADGE) | Q(type=ItemType.ITEM))

	class Meta:
		constraints = (models.UniqueConstraint(fields=("blueprint_item", "item"), name="blueprint_requirement_unique_blueprint_item_item"),)

	def __str__(self):
		return "%s needs %s" % (self.blueprint_item, super().__str__())

class MessageBodyCategory(models.Model):
	"""A category used for grouping message bodies in the "compose message" interface."""
	name = models.CharField(max_length=32)
	hidden = models.BooleanField()
	background_color = models.IntegerField()
	button_color = models.IntegerField()
	text_color = models.IntegerField()

	class Meta:
		verbose_name_plural = "Message body categories"

	def __str__(self):
		return self.name

class MessageBodyType(Enum):
	MODULE = auto()
	ITEM = auto()
	FRIEND = auto()
	REPLY = auto()
	USER = auto()
	SYSTEM = auto()
	BETA = auto()
	DEPRECATED_TYPE = auto()
	REWARD_CODE = auto()
	OTHER = auto()
	EXTERNAL_AWARD = auto()
	PROMO = auto()

class MessageBodyTheme(Enum):
	MLN = auto()
	MLN_SYSTEM = auto()
	MLN_BETA = auto()
	ROBOT_CHRONICLES = auto()
	COAST_GUARD = auto()
	CONSTRUCTION = auto()
	BIONICLE = auto()
	LEGO_UNIVERSE = auto()
	DICE_QUEST = auto()
	SPA = auto()
	LEGO_CLUB = auto()
	REAL_LIFE = auto()
	STAR_JUSTICE = auto()
	RACERS = auto()
	OTHER = auto()

class MessageBody(models.Model):
	"""
	A message text, consisting of subject and body.
	As MLN only allows sending prefabricated messages, using one of these is the only way of communication.
	Messages from Networkers also use this class.
	Some message texts have ready-made responses available, called easy replies.
	A common example is an easy reply of "Thanks", used by various message texts.
	"""
	category = models.ForeignKey(MessageBodyCategory, related_name="+", on_delete=models.CASCADE)
	type = EnumField(MessageBodyType, null=True, blank=True)
	theme = EnumField(MessageBodyTheme, null=True, blank=True)
	subject = models.CharField(max_length=128)
	text = models.TextField()
	notes = models.TextField(default="", blank=True)
	easy_replies = models.ManyToManyField("self", related_name="+", symmetrical=False, blank=True)

	class Meta:
		ordering = "subject", "text"
		verbose_name_plural = "Message bodies"

	def __str__(self):
		string = "%s: %s" % (self.subject, self.text)
		if len(string) > 100:
			string = string[:97]+"..."
		return string

class MessageReplyType(Enum):
	"""
	Message reply options, defining the combinations of reply and easy reply that can be used on a message.
	I'm not sure how these are associated with messages.
	Currently I just set a message to "normal & easy reply" if it has easy replies available, and "normal reply only" if it doesn't.
	"""
	NORMAL_REPLY_ONLY = 0
	NORMAL_AND_EASY_REPLY = 1
	EASY_REPLY_ONLY = 2
	NO_REPLY = 3

class MessageTemplate(models.Model):
	"""
	Defines a template for a message that will be sent by MLN.
	These templates can have attachments, but not a recipient.
	These are different from [Message], in that the latter have already been sent.
	"""
	body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)

	def __str__(self):
		result = self.body.subject
		for attachment in self.attachments.all():
			result += " + %s" % str(attachment)
		return result

class MessageTemplateAttachment(Stack):
	"""An attachment for a [MessageTemplate]."""
	template = models.ForeignKey(MessageTemplate, related_name="attachments", on_delete=models.CASCADE)

	class Meta:
		constraints = (models.UniqueConstraint(fields=("template", "item"), name="messsage_template_attachment_unique_template_item"),)

class ModuleEditorType(Enum):
	CONCERT_I_ARCADE = auto()
	CONCERT_II_ARCADE = auto()
	DELIVERY_ARCADE = auto()
	DESTRUCTOID_ARCADE = auto()
	DR_INFERNO_ROBOT_SIM = auto()
	FACTORY_GENERIC = auto()
	FACTORY_NON_GENERIC = auto()
	FRIEND_SHARE = auto()
	FRIENDLY_FELIX_CONCERT = auto()
	GALLERY_GENERIC = auto()
	GALLERY_NON_GENERIC = auto()
	GENERIC = auto()
	GROUP_PERFORMANCE = auto()
	HOP_ARCADE = auto()
	LOOP_SHOPPE = auto()
	NETWORKER_TEXT = auto()
	NETWORKER_TRADE = auto()
	PLASTIC_PELLET_INDUCTOR = auto()
	ROCKET_GAME = auto()
	SOUNDTRACK = auto()
	STICKER = auto()
	STICKER_SHOPPE = auto()
	TRADE = auto()
	TRIO_PERFORMANCE = auto()
	NETWORKER_PIC = auto()

class ModuleOutcome(Enum):
	"""When to distribute items. Used in module click handlers, like ModuleOwnerYield."""
	ARCADE = auto()  # after winning the game [eg, delivery]
	BATTLE = auto()  # after winning a battle  [eg, bee battle]
	NUM_CLICKS = auto()  # after a number of clicks [eg, Stardust Sticker]
	PROBABILITY = auto()  # can be 100% for a guarantee [eg, Wind Mill]

class ModuleHarvestYield(models.Model):
	"""Defines the item the module "grows", its harvest cap, its growth rate, and the click growth rate."""
	item = models.OneToOneField(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.MODULE))
	yield_item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.BLUEPRINT) | Q(type=ItemType.ITEM))
	max_yield = models.PositiveSmallIntegerField()
	yield_per_day = models.PositiveSmallIntegerField()
	clicks_per_yield = models.PositiveSmallIntegerField()

	def __str__(self):
		return str(self.item)

class ModuleInfo(models.Model):
	"""Stores whether the module is executable, setupable, and its editor type. The editor type defines which save data the module uses."""
	item = models.OneToOneField(ItemInfo, related_name="module_info", on_delete=models.CASCADE)
	is_executable = models.BooleanField()
	editor_type = EnumField(ModuleEditorType, null=True, blank=True)
	click_outcome = EnumField(ModuleOutcome, null=True, blank=True)  # null means unclickable

	def __str__(self):
		return str(self.item)

class ModuleSetupCost(Stack):
	"""
	Defines the cost owner will have to pay to set up a module.
	This can be retrieved by the owner as long as the module isn't ready for harvest or hasn't been executed.
	"""
	module_item = models.ForeignKey(ItemInfo, related_name="setup_costs", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.MODULE))
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to={"type": ItemType.ITEM})

	class Meta:
		constraints = (models.UniqueConstraint(fields=("module_item", "item"), name="module_setup_cost_unique_module_item_item"),)

class NetworkerFriendshipCondition(models.Model):
	"""Stores what a networker requires to accept a friend request, and the messages to be sent on success or failure."""
	networker = models.OneToOneField(User, related_name="friendship_condition", on_delete=models.CASCADE, limit_choices_to={"profile__is_networker": True})
	condition = models.ForeignKey(ItemInfo, related_name="+", blank=True, null=True, on_delete=models.SET_NULL, limit_choices_to=Q(type=ItemType.BADGE) | Q(type=ItemType.BLUEPRINT) | Q(type=ItemType.ITEM) | Q(type=ItemType.MASTERPIECE))
	success_body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)
	failure_body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)

class NetworkerFriendshipConditionSource(models.Model):
	"""Not related to MLN's core data model: Sources for manually associated friendship conditions."""
	condition = models.OneToOneField(NetworkerFriendshipCondition, related_name="source", on_delete=models.CASCADE)
	source = models.TextField()

	def __str__(self):
		return self.source

class NetworkerPageSource(models.Model):
	"""Documentation only: Note whether a reconstructed networker page has a graphical source, or is tentatively reconstructed from a description."""
	networker = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE, limit_choices_to={"profile__is_networker": True})
	source = models.TextField()

class Question(models.Model):
	"""A question for the "About me" section."""
	text = models.CharField(max_length=64)
	mandatory = models.BooleanField()

	def __str__(self):
		return self.text

class Answer(models.Model):
	"""An answer to an "About me" question."""
	question = models.ForeignKey(Question, related_name="+", on_delete=models.CASCADE)
	text = models.CharField(max_length=64)

	def __str__(self):
		return self.text

class Color(models.Model):
	"""A color, used for page and module backgrounds."""
	color = models.IntegerField()

	def __str__(self):
		return hex(self.color)

class ModuleSkin(models.Model):
	"""A skin (background pattern) of a module."""
	name = models.CharField(max_length=64)

	def __str__(self):
		return self.name

class StartingStack(Stack):
	"""A stack that users start off with in their inventory when they create an account."""
	item = models.OneToOneField(ItemInfo, related_name="+", on_delete=models.CASCADE)

class NetworkerReply(models.Model):
	template = models.ForeignKey(MessageTemplate, related_name="+", on_delete=models.CASCADE)
	networker = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE, blank=True, null=True, limit_choices_to={"profile__is_networker": True})
	trigger_body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE, null=True, blank=True)
	trigger_attachment = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, null=True, blank=True)
	trigger_item_obtained = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, null=True, blank=True, limit_choices_to=Q(type=ItemType.BADGE) | Q(type=ItemType.BLUEPRINT) | Q(type=ItemType.ITEM) | Q(type=ItemType.MASTERPIECE) | Q(type=ItemType.MODULE) | Q(type=ItemType.MOVIE) | Q(type=ItemType.SKIN))

	class Meta:
		verbose_name_plural = "Networker replies"

	def __str__(self):
		return "Reply when sending %s to %s: %s" % (self.trigger_attachment or self.trigger_body, self.networker, self.template.body.subject)

	def should_reply(self, message, attachment):
		return (
			(self.trigger_body is not None and message.body == self.trigger_body) or
			(self.trigger_attachment is not None and attachment is not None and attachment.item == self.trigger_attachment)
		)

class NetworkerMessageTriggerLegacy(models.Model):
	"""Currently meant for devs to collect data on triggers, later to be properly integrated into the system."""
	networker = models.CharField(max_length=64, blank=True, null=True)
	body = models.ForeignKey(MessageBody, related_name="+", on_delete=models.CASCADE)
	trigger = models.TextField(blank=True, null=True)
	source = models.TextField()
	notes = models.TextField(blank=True, null=True)
	updated = models.ForeignKey(NetworkerReply, related_name="legacy", on_delete=models.SET_NULL, blank=True, null=True)

	def __str__(self):
		return "From %s: %s" % (self.networker, self.body)

class NetworkerMessageAttachmentLegacy(Stack):
	"""A stack to be attached to a networker message."""
	trigger = models.ForeignKey(NetworkerMessageTriggerLegacy, related_name="attachments", on_delete=models.CASCADE)
	updated = models.ForeignKey(MessageTemplateAttachment, related_name="legacy", on_delete=models.CASCADE, blank=True, null=True)

	class Meta:
		constraints = (models.UniqueConstraint(fields=("trigger", "item"), name="networker_message_attachment_unique_trigger_item"),)
