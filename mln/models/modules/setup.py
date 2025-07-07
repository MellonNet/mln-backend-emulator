from ..utils import *
from ..items import *

class ModuleSetupCost(Stack):
	"""
	Defines the cost owner will have to pay to set up a module.
	This can be retrieved by the owner as long as the module isn't ready for harvest or hasn't been executed.
	"""
	module_item = models.ForeignKey(ItemInfo, related_name="setup_costs", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.MODULE))
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to={"type": ItemType.ITEM})

	class Meta:
		constraints = (models.UniqueConstraint(fields=("module_item", "item"), name="module_setup_cost_unique_module_item_item"),)
