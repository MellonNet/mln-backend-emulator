"""The model for modules. Module settings are in their own files."""
import random

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.timezone import now

from .dynamic import DAY, get_or_none
from .static import ArcadePrize, ItemInfo, ItemType, ModuleEditorType, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleYieldInfo

class Module(models.Model):
	"""
	A module instance on a user's page.
	This does not represent a stack of modules in the user's inventory, for that, see InventoryStack.
	"""
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to={"type": ItemType.MODULE})
	owner = models.ForeignKey(User, related_name="modules", on_delete=models.CASCADE)
	pos_x = models.PositiveSmallIntegerField(null=True, blank=True, validators=(MaxValueValidator(2),))
	pos_y = models.PositiveSmallIntegerField(null=True, blank=True, validators=(MaxValueValidator(3),))
	last_harvest_time = models.DateTimeField(default=now)
	clicks_since_last_harvest = models.PositiveSmallIntegerField(default=0)
	total_clicks = models.PositiveIntegerField(default=0)
	is_setup = models.BooleanField(default=False) # this is actually only relevant for some modules, refactor?

	def __str__(self):
		return "%s's %s at pos (%i, %i), %i clicks" % (self.owner, self.item.name, self.pos_x, self.pos_y, self.total_clicks)

	def clean(self):
		if self.owner.modules.filter(pos_x=self.pos_x, pos_y=self.pos_y).exclude(id=self.id).exists():
			raise ValidationError("User %s already has a module at position %i %i" % (self.owner, self.pos_x, self.pos_y))

	def get_info(self):
		"""Get the ModuleInfo for this module."""
		return ModuleInfo.objects.get(item_id=self.item_id)

	def _calc_yield_info(self):
		"""Calculate the yield of this module (how many items you can harvest), as well as the time and clicks that remain."""
		info = self.get_info()
		if info.is_setupable and not self.is_setup:
			return 0, 0, 0
		yield_info = get_or_none(ModuleYieldInfo, item_id=self.item_id)
		if yield_info is None:
			return 0, 0, 0
		time_since_harvest = now() - self.last_harvest_time
		if yield_info.yield_per_day == 0:
			time_yield = 0
			time_remainder = time_since_harvest
		else:
			time_yield, time_remainder = divmod(time_since_harvest, (DAY / yield_info.yield_per_day))
		if yield_info.clicks_per_yield == 0:
			click_yield = 0
			click_remainder = self.clicks_since_last_harvest
		else:
			click_yield, click_remainder = divmod(self.clicks_since_last_harvest, yield_info.clicks_per_yield)
		final_yield = min(time_yield + click_yield, yield_info.max_yield)
		return final_yield, time_remainder, click_remainder

	def calc_yield_qty(self):
		"""Calculate the yield of this module."""
		return self._calc_yield_info()[0]

	def get_yield_item_id(self):
		"""Get the id of the item this module yields."""
		return ModuleYieldInfo.objects.get(item_id=self.item_id).yield_item_id

	def harvest(self):
		"""
		Harvest the module.
		Place the yielded items into the owner's inventory, and update time and click counts.
		If the module was set up, the set up item will be lost at this point.
		"""
		harvest_qty, time_remainder, click_remainder = self._calc_yield_info()
		self.owner.profile.add_inv_item(self.get_yield_item_id(), qty=harvest_qty)
		self.last_harvest_time = now() - time_remainder
		self.clicks_since_last_harvest = click_remainder
		self.is_setup = False
		self.save()

	def vote(self, voter):
		"""
		Vote on the module. Add a click to the module, and remove one from the voter's available votes.
		Raise ValueError if the voter is the module owner.
		"""
		if voter == self.owner:
			raise ValueError("Can't vote on own module")
		if voter.profile.available_votes <= 0:
			raise RuntimeError("Voter has no votes left")
		self.clicks_since_last_harvest += 1
		self.total_clicks += 1
		self.save()
		voter.profile.available_votes -= 1
		voter.profile.save()

	def setup(self):
		"""
		Set up the module with items.
		Raise RuntimeError if the owner doesn't have the required items in their inventory.
		"""
		if self.is_setup:
			return
		if ModuleSetupTrade in self.get_settings_classes():
			trade = ModuleSetupTrade.objects.get(module=self)
			self.owner.profile.remove_inv_item(trade.give_item_id, trade.give_qty)
		else:
			costs = ModuleSetupCost.objects.filter(module_item_id=self.item_id)
			for cost in costs:
				self.owner.profile.remove_inv_item(cost.item_id, cost.qty)
		self.is_setup = True
		self.last_harvest_time = now()
		self.save()

	def teardown(self):
		"""Remove the set up items."""
		if not self.is_setup:
			return
		if ModuleSetupTrade in self.get_settings_classes():
			trade = ModuleSetupTrade.objects.get(module=self)
			self.owner.profile.add_inv_item(trade.give_item_id, trade.give_qty)
		else:
			for cost in ModuleSetupCost.objects.filter(module_item_id=self.item_id):
				self.owner.profile.add_inv_item(cost.item_id, cost.qty)
		self.is_setup = False
		self.save()

	def execute(self, executer):
		"""Execute the module. If there is an execution cost, remove the cost from the user."""
		self.vote(executer)
		if ModuleSetupTrade in self.get_settings_classes():
			trade = ModuleSetupTrade.objects.get(module=self)
			executer.profile.remove_inv_item(trade.request_item_id, trade.request_qty)
			executer.profile.add_inv_item(trade.give_item_id, trade.give_qty)
			self.owner.profile.add_inv_item(trade.request_item_id, trade.request_qty)
			self.is_setup = False
			# give item was already taken from owner at setup
		else:
			costs = ModuleExecutionCost.objects.filter(module_item_id=self.item_id)
			for cost in costs:
				executer.profile.remove_inv_item(cost.item_id, cost.qty)
		self.save()

	def select_arcade_prize(self, user):
		"""Select a random arcade prize for an arcade winner."""
		chance = random.randrange(100)
		sum = 0
		for prize in ArcadePrize.objects.filter(module_item_id=self.item_id):
			sum += prize.success_rate
			if sum > chance:
				user.profile.add_inv_item(prize.item_id, prize.qty)
				return prize
		raise RuntimeError("Should have chosen a prize but didn't for some reason")

	def get_settings_classes(self):
		"""Get the save data classes for this module."""
		info = self.get_info()
		return module_settings_classes[info.editor_type]

from .module_settings import ModuleSaveGeneric, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupGroupPerformance, ModuleSetupTrade, ModuleSetupTrioPerformance
from .module_settings_arcade import ModuleSaveConcertArcade, ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade

"""Settings class registry. This links module editor types to settings classes."""
module_settings_classes = {
	ModuleEditorType.CONCERT_I_ARCADE: (ModuleSaveConcertArcade,),
	ModuleEditorType.CONCERT_II_ARCADE: (ModuleSaveConcertArcade,),
	ModuleEditorType.DELIVERY_ARCADE: (ModuleSaveDeliveryArcade,),
	ModuleEditorType.DESTRUCTOID_ARCADE: (ModuleSaveDestructoidArcade,),
	ModuleEditorType.DR_INFERNO_ROBOT_SIM: (ModuleSaveDestructoidArcade,),
	ModuleEditorType.FACTORY_GENERIC: (ModuleSaveGeneric, ModuleSaveUGC),
	ModuleEditorType.FACTORY_NON_GENERIC: (ModuleSaveUGC,),
	ModuleEditorType.FRIEND_SHARE: (ModuleSaveGeneric, ModuleSetupFriendShare),
	ModuleEditorType.FRIENDLY_FELIX_CONCERT: (ModuleSaveConcertArcade,),
	ModuleEditorType.GALLERY_GENERIC: (ModuleSaveGeneric, ModuleSaveUGC),
	ModuleEditorType.GALLERY_NON_GENERIC: (ModuleSaveUGC,),
	ModuleEditorType.GENERIC: (ModuleSaveGeneric,),
	ModuleEditorType.GROUP_PERFORMANCE: (ModuleSaveGeneric, ModuleSetupGroupPerformance),
	ModuleEditorType.HOP_ARCADE: (ModuleSaveHopArcade,),
	ModuleEditorType.LOOP_SHOPPE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.NETWORKER_TEXT: (ModuleSaveGeneric, ModuleSaveNetworkerText),
	ModuleEditorType.NETWORKER_TRADE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.PLASTIC_PELLET_INDUCTOR: (ModuleSaveUGC,),
	ModuleEditorType.ROCKET_GAME: (ModuleSaveSticker, ModuleSaveRocketGame),
	ModuleEditorType.SOUNDTRACK: (ModuleSaveGeneric, ModuleSaveSoundtrack),
	ModuleEditorType.STICKER: (ModuleSaveSticker,),
	ModuleEditorType.STICKER_SHOPPE: (ModuleSetupTrade,),
	ModuleEditorType.TRADE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.TRIO_PERFORMANCE: (ModuleSaveGeneric, ModuleSetupTrioPerformance),
}
