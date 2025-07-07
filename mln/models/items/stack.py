from ..utils import *

from .info import *

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

class StartingStack(Stack):
	"""A stack that users start off with in their inventory when they create an account."""
	item = models.OneToOneField(ItemInfo, related_name="+", on_delete=models.CASCADE)

class InventoryStack(Stack):
	"""A stack of items in the user's inventory."""
	owner = models.ForeignKey(User, related_name="inventory", on_delete=models.CASCADE)

	class Meta:
		constraints = (models.UniqueConstraint(fields=("owner", "item"), name="inventory_stack_unique_owner_item"),)

	def __str__(self):
		return "%s's stack of %s" % (self.owner, super().__str__())
