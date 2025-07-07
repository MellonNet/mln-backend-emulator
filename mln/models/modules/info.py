from ..utils import *
from ..items import *

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

class ModuleInfo(models.Model):
	"""Stores whether the module is executable, setupable, and its editor type. The editor type defines which save data the module uses."""
	item = models.OneToOneField(ItemInfo, related_name="module_info", on_delete=models.CASCADE)
	is_executable = models.BooleanField()
	editor_type = EnumField(ModuleEditorType, null=True, blank=True)
	click_outcome = EnumField(ModuleOutcome, null=True, blank=True)  # null means unclickable

	def __str__(self):
		return str(self.item)
