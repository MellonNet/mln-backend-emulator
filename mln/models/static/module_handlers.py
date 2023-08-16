import random

from django.db import models
from django.db.models import Q

from .static import ItemInfo, ItemType, MessageTemplate, ModuleOutcome, Stack

from ...services.friend import choose_friend
from ...services.inventory import add_inv_item, assert_has_item, remove_inv_item
from ...services.message import send_template

class ModuleClickHandler(models.Model): 
	"""A handler that executes an action when a module is clicked."""
	module_item = models.ForeignKey(ItemInfo, related_name="%(class)ss", on_delete=models.CASCADE, limit_choices_to=Q(type=ItemType.MODULE))
	probability = models.PositiveSmallIntegerField(default=100)

	class Meta: abstract = True

	def on_click(self, module, clicker): pass

class ModuleMessage(ModuleClickHandler): 
	"""
	A message that may be sent to the module owner's friends when clicked.
	These messages usually, but not necessarily, include an attachment with rewards.
	"""
	message = models.OneToOneField(MessageTemplate, related_name="+", on_delete=models.CASCADE)

	class Meta:
		constraints = (models.UniqueConstraint(fields=("module_item",), name="module_message_unique_module_item"),)

	def on_click(self, module, clicker):
		if random.random()*100 >= self.probability: return 
		random_friend = choose_friend(module.owner)
		if random_friend is None: return  # lol ain't got no friends :(
		print("Sending mail...")
		send_template(self.message, module.owner, clicker)

class ModuleClickYield(ModuleClickHandler, Stack): 
	"""A [ModuleClickHandler] that transfers items in a [Stack]."""
	class Meta: abstract = True

	def should_yield(self, module): 
		"""
		Returns whether this handler should react to the module based on its outcome. 

		For example, arcade modules immediately give the owner a token, but wait until
		the outcome of the game is known before rewarding the user. Similarly, battle
		modules need to know who won before giving out rewards.
		"""
		pass

	def distribute_items(self, module, clicker): pass

	def on_click(self, module, clicker):
		if self.should_yield(module): self.distribute_items(module, clicker)

class ModuleExecutionCost(ModuleClickYield):
	"""
	Defines the cost guests will have to pay to click on the module.
	The paid items are typically not transferred to the module owner, they are deleted from the system.
	"""	
	class Meta:
		constraints = (models.UniqueConstraint(fields=("module_item", "item"), name="module_execution_cost_unique_module_item_item"),)

	def should_yield(self, module): return True

	def distribute_items(self, module, clicker): 
		assert_has_item(clicker, self.item_id, self.qty)
		remove_inv_item(clicker, self.item_id, self.qty)

class ModuleGuestYield(ModuleClickYield):
	"""
	Defines the item(s) granted to guests when they click on the module.
	The items can come from the setup cost or are generated by MLN. 
	"""

	class Meta:
		constraints = (models.UniqueConstraint(fields=("module_item", "item"), name="module_guest_yield_unique_module_item_item"),)

	def should_yield(self, module): 
		outcome = self.module_item.module_info.click_outcome  # cache the related_name query
		if outcome == ModuleOutcome.PROBABILITY: return True
		elif outcome == ModuleOutcome.NUM_CLICKS: return True
		elif outcome == ModuleOutcome.BATTLE: return module.did_guest_win
		elif outcome == ModuleOutcome.ARCADE: return module.did_guest_win
		else: raise RuntimeError("Unknown module outcome: %s" % outcome)

	def distribute_items(self, module, clicker): 
		add_inv_item(clicker, self.item_id, self.qty)

class ModuleOwnerYield(ModuleClickYield):
	"""
	Defines the item(s) granted to the owner of the module when clicked. 
	The items can come from the execution cost or are generated by MLN. 
	"""

	class Meta:
		constraints = (models.UniqueConstraint(fields=("module_item", "item"), name="module_owner_yield_unique_module_item_item"),)

	def should_yield(self, module):
		outcome = self.module_item.module_info.click_outcome  # cache the related_name query
		if outcome == ModuleOutcome.PROBABILITY: return True
		elif outcome == ModuleOutcome.NUM_CLICKS: return False # Handled by clicks calculating
		elif outcome == ModuleOutcome.BATTLE: return not module.did_guest_win
		elif outcome == ModuleOutcome.ARCADE: return True
		else: raise RuntimeError("Unknown module outcome: %s" % outcome)

	def distribute_items(self, module, clicker): 	
		module.add_to_harvest(self.qty)

# Excluding [ModuleGuestYield], those are handled separately.
CLICK_HANDLERS = (ModuleMessage, ModuleExecutionCost, ModuleOwnerYield)
