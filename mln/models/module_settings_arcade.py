"""Models for arcade module save data."""
from enum import auto, Enum

from django.core.validators import MaxValueValidator
from django.db import models

from .module import Module
from .static import EnumField

class ModuleSaveArcade(models.Model):
	"""
	Abstract base class for arcade save data.
	Saves whether the owner has successfully played the game.
	This is needed for all arcade games to make the module executable, to make sure the game is actually playable.
	"""
	owner_played = models.BooleanField()

	class Meta:
		abstract = True

class ModuleSaveConcertArcade(ModuleSaveArcade):
	"""
	Save data for concert arcade modules.
	Saves the background and arrow skin, and the arrows for the game.
	Since the game consists of a 64 x 4 grid of arrows, and each arrow is either there or not, I use a 64-bit integer for each column.
	"""
	module = models.OneToOneField(Module, related_name="save_concert_arcade", on_delete=models.CASCADE)
	background_skin = models.PositiveSmallIntegerField(validators=(MaxValueValidator(2),))
	arrowset_skin = models.PositiveSmallIntegerField(validators=(MaxValueValidator(2),))
	arrows_left = models.BigIntegerField()
	arrows_down = models.BigIntegerField()
	arrows_up = models.BigIntegerField()
	arrows_right = models.BigIntegerField()

def DeliveryPosField(*args, **kwargs):
	return models.PositiveSmallIntegerField(validators=(MaxValueValidator(25),))

class DeliveryArcadeTile(models.Model):
	"""
	A tile in a delivery arcade game.
	Saves the position of the tile as well as its tile ID.
	I store both pathway and scenery tiles in the same ID field, unlike the flash files, which have separate tile_<id> and scen_<id> names for them.
	To store them both in the same field without collisions, scenery tiles get the 5th bit ( |= 32 ) set.
	"""
	module = models.ForeignKey(Module, related_name="tiles", on_delete=models.CASCADE)
	x = DeliveryPosField()
	y = DeliveryPosField()
	tile_id = models.PositiveSmallIntegerField()

	def __str__(self):
		return "%s: Tile %i at %i, %i" % (self.module, self.tile_id, self.x, self.y)

class ModuleSaveDeliveryArcade(ModuleSaveArcade):
	"""
	Save data for the delivery arcade game.
	The delivery game grid is too large to use a compact storage method like with the other arcades, so delivery saves its tiles as actual database entries (see DeliveryArcadeTile).
	However houses and the start point are handled a bit differently from normal tiles, they are required for a playable game and can only exist once, so they're stored in this model.
	Also stored is the time the owner needed to successfully play the game, which is used as a countdown for players later.
	"""
	module = models.OneToOneField(Module, related_name="save_delivery_arcade", on_delete=models.CASCADE)
	timer = models.PositiveSmallIntegerField()
	house_0_x = DeliveryPosField(null=True, blank=True)
	house_0_y = DeliveryPosField(null=True, blank=True)
	house_1_x = DeliveryPosField(null=True, blank=True)
	house_1_y = DeliveryPosField(null=True, blank=True)
	house_2_x = DeliveryPosField(null=True, blank=True)
	house_2_y = DeliveryPosField(null=True, blank=True)
	start_x = DeliveryPosField(null=True, blank=True)
	start_y = DeliveryPosField(null=True, blank=True)

class DestructoidCharacterSkin(Enum):
	"""
	Skins for the character in the destructoid arcade game.
	The robot simulator version doesn't allow choosing a skin and uses the "man" skin with a different sprite.
	"""
	MAN = auto()
	LIZARD = auto()

class DestructoidBlockSkin(Enum):
	"""
	Skins for the blocks in the destructoid arcade game.
	The robot simulator version doesn't allow choosing a skin and uses the "pbrick" skin with a different sprite.
	"""
	PBRICK = auto()
	SKULL = auto()

class ModuleSaveDestructoidArcade(ModuleSaveArcade):
	"""
	Save data for the destructoid arcade game.
	The robot simulator version uses the same save data, the only changes are the sprites used, and the option of choosing a skin not being available.
	The game grid is 11 x 3 x 3 bits, which doesn't make this as suitable for compact storage as the concert games, but it's still somewhat reasonable, and 3 64-bit integers can be used, one for each row.
	Unfortunately only 33 bits of the 64 bits are used.
	However, since the game data is serialized as the entire grid, including grid entries with no blocks, saving data this way is easier than saving it in database entries and filling up the remaining values with null entries in serialization.
	"""
	module = models.OneToOneField(Module, related_name="save_destructoid_arcade", on_delete=models.CASCADE)
	energy_used = models.PositiveSmallIntegerField()
	character_skin = EnumField(DestructoidCharacterSkin)
	block_skin = EnumField(DestructoidBlockSkin)
	background_skin = models.PositiveSmallIntegerField()
	top = models.BigIntegerField()
	middle = models.BigIntegerField()
	bottom = models.BigIntegerField()

class HopArcadeElement(Enum):
	"""Game elements in hop arcade games."""
	POWERUP_1 = auto()
	POWERUP_2 = auto()
	BIRD = auto()
	SNAKE = auto()
	BRICKS = auto()
	ROCKS = auto()

class ModuleSaveHopArcade(ModuleSaveArcade):
	"""
	Save data for the hop arcade game.
	The hop arcade game grid consists of 30 x 3 x 3 bits, which makes it possible to store it efficiently as 3 32-bit integers in each row.
	This also makes serialization easier, as the entire grid is serialized, including grid entries without a set game element.
	"""
	module = models.OneToOneField(Module, related_name="save_hop_arcade", on_delete=models.CASCADE)
	top_0 = models.IntegerField()
	top_1 = models.IntegerField()
	top_2 = models.IntegerField()
	middle_0 = models.IntegerField()
	middle_1 = models.IntegerField()
	middle_2 = models.IntegerField()
	bottom_0 = models.IntegerField()
	bottom_1 = models.IntegerField()
	bottom_2 = models.IntegerField()
