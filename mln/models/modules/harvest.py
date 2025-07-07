from ..utils import *
from ..items import *

class ModuleHarvestYield(models.Model):
	"""Defines the item the module "grows", its harvest cap, its growth rate, and the click growth rate."""
	item = models.OneToOneField(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.MODULE))
	yield_item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.BLUEPRINT) | Q(type=ItemType.ITEM))
	max_yield = models.PositiveSmallIntegerField()
	yield_per_day = models.PositiveSmallIntegerField()
	clicks_per_yield = models.PositiveSmallIntegerField()

	def __str__(self):
		return str(self.item)
