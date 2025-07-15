from ..utils import *

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
