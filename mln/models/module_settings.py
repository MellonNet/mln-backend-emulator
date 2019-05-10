"""Models for module settings. Arcade module settings are in their own file."""
from enum import auto, Enum

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from ..services.friend import are_friends
from ..services.inventory import assert_has_item
from .module import Module
from .static import Color, EnumField, ItemInfo, ItemType, ModuleSkin

class ModuleSaveGeneric(models.Model):
	"""
	Generic save data for modules.
	This is the most common save data, present on all modules without special features, and on a number of those with special features as well.
	It saves module background color and module background skin (background pattern).
	"""
	module = models.OneToOneField(Module, related_name="save_generic", on_delete=models.CASCADE)
	skin = models.ForeignKey(ModuleSkin, related_name="+", on_delete=models.CASCADE, null=True, blank=True)
	color = models.ForeignKey(Color, related_name="+", on_delete=models.CASCADE, null=True, blank=True)

class ModuleSaveNetworkerPic(models.Model):
	"""
	Save data for networker pic modules.
	Networker pic modules used to be normal sticker modules in the original game, but this didn't model their contents well, as networker pic modules always have exactly one sticker at a fixed position/scale/rotation/depth.
	If/When we break compatibility with the flash client we should change the modeling further so that the pictures aren't stickers (possibly not even items) anymore. The pictures aren't supposed to be used by users in a sticker module anyway.
	"""
	module = models.OneToOneField(Module, related_name="save_networker_pic", on_delete=models.CASCADE)
	picture = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to={"type": ItemType.STICKER})

class ModuleSaveNetworkerText(models.Model):
	"""
	Save data for the networker text module used for networker descriptions and quotes.
	This is the only part of MLN where free text entry is possible.
	"""
	module = models.OneToOneField(Module, related_name="save_networker_text", on_delete=models.CASCADE)
	text = models.TextField()

class RocketGameTheme(Enum):
	"""Themes for the rocket game, determining the sprites of game objects used."""
	SPACE = auto()
	PUNK = auto()
	MARS = auto()

class ModuleSaveRocketGame(models.Model):
	"""Save data for the rocket game. The rocket game is fairly straightforward, the only thing you can choose is the theme."""
	module = models.OneToOneField(Module, related_name="save_rocket_game", on_delete=models.CASCADE)
	theme = EnumField(RocketGameTheme)

class ModuleSaveSoundtrack(models.Model):
	"""Save data for the soundtrack module, consisting of a 4 x 4 grid of loop item ids and pan values, added programmatically below."""
	module = models.OneToOneField(Module, related_name="save_soundtrack", on_delete=models.CASCADE)

	def clean(self):
		for i in range(4):
			for j in range(4):
				item_id = getattr(self, "sound_%i_%i_id" % (i, j))
				if item_id is not None:
					assert_has_item(self.module.owner, item_id, field_name="sound_%i_%i" % (i, j))

# this looks weird but it's the simplest way to do this
for i in range(4):
	for j in range(4):
		ModuleSaveSoundtrack.add_to_class("sound_%i_%i" % (i, j), models.ForeignKey(ItemInfo, null=True, blank=True, related_name="+", on_delete=models.CASCADE, limit_choices_to={"type": ItemType.LOOP}))
		ModuleSaveSoundtrack.add_to_class("sound_%i_%i_pan" % (i, j), models.SmallIntegerField(validators=(MinValueValidator(-100), MaxValueValidator(100))))

class ModuleSaveSticker(models.Model):
	"""
	A sticker in a sticker module.
	Saved are the sticker item, the position, scale, rotation, and depth (which sticker is drawn first).
	"""
	module = models.ForeignKey(Module, related_name="save_sticker", on_delete=models.CASCADE)
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.BACKGROUND) | Q(type=ItemType.STICKER))
	x = models.FloatField()
	y = models.FloatField()
	scale_x = models.SmallIntegerField()
	scale_y = models.SmallIntegerField()
	rotation = models.SmallIntegerField()
	depth = models.SmallIntegerField()

	def clean(self):
		if self.item.type == ItemType.STICKER:
			assert_has_item(self.module.owner, self.item_id, field_name="item")

class ModuleSaveUGC(models.Model):
	"""
	Save data for modules with user-generated content (UGC): gallery, factory, and creation lab.
	The actual data is saved in another database, MLN only stores an ID that will be requested from the other DB by the module.
	"""
	module = models.OneToOneField(Module, related_name="save_ugc", on_delete=models.CASCADE)
	ref = models.PositiveIntegerField() # weak link to other db

class ModuleSetupFriendShare(models.Model):
	"""Save data for 2-person friend share modules, like the BFF module."""
	module = models.OneToOneField(Module, related_name="setup_friend_share", on_delete=models.CASCADE)
	friend = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)

	def clean(self):
		if not are_friends(self.module.owner, self.friend_id):
			raise ValidationError({"friend": "User with ID %i is not a friend of the module owner" % self.friend_id})

class ModuleSetupGroupPerformance(models.Model):
	"""Save data for the 4-person group performance module."""
	module = models.OneToOneField(Module, related_name="setup_group_performance", on_delete=models.CASCADE)
	friend_0 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)
	friend_1 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)
	friend_2 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)

	def clean(self):
		friends = set()
		for name in ("friend_0", "friend_1", "friend_2"):
			user_id = getattr(self, name+"_id")
			if not are_friends(self.module.owner, user_id):
				raise ValidationError({name: "User %s is not a friend of the module owner" % getattr(self, name)})
			friends.add(user_id)
		if len(friends) != 3:
			raise ValidationError("Duplicate friends specified")

class ModuleSetupTrade(models.Model):
	"""
	Save data for trade modules, including networker trade modules.
	Saved are the item and quantity the owner offers and the item and quantity the owner seeks.
	"""
	module = models.OneToOneField(Module, related_name="setup_trade", on_delete=models.CASCADE)
	give_item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE)
	give_qty = models.PositiveSmallIntegerField()
	request_item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE)
	request_qty = models.PositiveSmallIntegerField()

class ModuleSetupTrioPerformance(models.Model):
	"""Save data for the 3-person trio performance module."""
	module = models.OneToOneField(Module, related_name="setup_trio_performance", on_delete=models.CASCADE)
	friend_0 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)
	friend_1 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)

	def clean(self):
		friends = set()
		for name in ("friend_0", "friend_1"):
			user_id = getattr(self, name+"_id")
			if not are_friends(self.module.owner, user_id):
				raise ValidationError({name: "User %s is not a friend of the module owner" % getattr(self, name)})
			friends.add(user_id)
		if len(friends) != 2:
			raise ValidationError("Duplicate friends specified")
