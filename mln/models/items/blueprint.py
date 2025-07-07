from ..utils import *
from .info import *
from .stack import *

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
