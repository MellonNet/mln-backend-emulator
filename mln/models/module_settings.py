"""Models for module settings. Arcade module settings are in their own file."""
from enum import auto, Enum

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

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

# this looks weird but it's the simplest way to do this
for i in range(4):
	for j in range(4):
		ModuleSaveSoundtrack.add_to_class("sound_%i_%i" % (i, j), models.ForeignKey(ItemInfo, null=True, blank=True, related_name="+", on_delete=models.CASCADE, limit_choices_to={"type": ItemType.LOOP}))
		ModuleSaveSoundtrack.add_to_class("sound_%i_%i_pan" % (i, j), models.SmallIntegerField())

class ModuleSaveSticker(models.Model):
	"""
	A sticker in a sticker module.
	Saved are the sticker item, the position, scale, rotation, and depth (which sticker is drawn first).
	Networker picture modules are actually just sticker modules as well, and their pictures are stickers.
	"""
	module = models.ForeignKey(Module, related_name="save_sticker", on_delete=models.CASCADE)
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.BACKGROUND) | Q(type=ItemType.STICKER))
	x = models.FloatField()
	y = models.FloatField()
	scale_x = models.SmallIntegerField()
	scale_y = models.SmallIntegerField()
	rotation = models.SmallIntegerField()
	depth = models.SmallIntegerField()

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

class ModuleSetupGroupPerformance(models.Model):
	"""Save data for the 4-person group performance module."""
	module = models.OneToOneField(Module, related_name="setup_group_performance", on_delete=models.CASCADE)
	friend_0 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)
	friend_1 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)
	friend_2 = models.OneToOneField(User, related_name="+", on_delete=models.CASCADE)

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
