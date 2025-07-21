"""The model for modules. Module settings are in their own files."""
import random

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta

from .dynamic import DAY, get_or_none
from .dynamic import FriendshipStatus
from ..static import ItemInfo, ItemType, MessageTemplate, ModuleEditorType, ModuleHarvestYield, ModuleInfo, ModuleOutcome, ModuleSetupCost, Stack
from ..static.module_handlers import CLICK_HANDLERS

from ...services.inventory import add_inv_item, assert_has_item, remove_inv_item
from ...services.friend import choose_friend
from ...services.message import send_template

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
	yield_since_last_harvest = models.PositiveSmallIntegerField(default=0)
	total_clicks = models.PositiveIntegerField(default=0)
	is_setup = models.BooleanField(null=True, blank=True, default=False)
	did_guest_win = None  # NOT a ForeignKey, is temporary storage for each click

	class Meta:
		constraints = (models.UniqueConstraint(fields=("owner", "pos_x", "pos_y"), name="module_unique_owner_pos"),)

	def __str__(self):
		return "%s's %s at pos (%s, %s), %i clicks" % (self.owner, self.item.name, self.pos_x, self.pos_y, self.total_clicks)

	def save(self, *args, **kwargs):
		"""Check if module isn't set up when it doesn't even need to be."""
		if not self._needs_setup() and self.is_setup is False:
			self.is_setup = None
		super().save(*args, **kwargs)

	def _calc_yield_info(self):
		"""Calculate the yield of this module (how many items you can harvest), as well as the time and clicks that remain."""
		yield_info = get_or_none(ModuleHarvestYield, item_id=self.item_id)
		if yield_info is None:
			return self.yield_since_last_harvest, timedelta(seconds=0), 0
		if self._needs_setup() and not self.is_setup:
			return min(self.yield_since_last_harvest, yield_info.max_yield), timedelta(seconds=0), 0
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
		final_yield = min(time_yield + click_yield + self.yield_since_last_harvest, yield_info.max_yield)
		return final_yield, time_remainder, click_remainder

	def _get_yield(self, yields):
		"""Chooses an available yield based on its assigned probability."""
		if len(yields) == 0: return None  # no yield for clicking
		elif len(yields) == 1:  # standard, one-item yield
			result = yields[0]
			if random.random() < (result.probability / 100): return result
			else: return None
		else:  # lottery
			random_number = random.randrange(100)
			sum = 0
			for prize in yields:
				sum += prize.probability
				if sum > random_number:
					return prize
			else:
				raise RuntimeError(f"Couldn't choose a yield for {self}. Possible yields: {yields}")

	def _needs_setup(self):
		return self.item.module_info.editor_type == ModuleEditorType.TRADE or self.item.setup_costs.exists()

	def _validate_click(self, clicker):
		if clicker == self.owner:  # user can't click on own module
			raise ValueError("Can't vote on own module")
		elif clicker.profile.available_votes <= 0:  # user must have clicks
			raise RuntimeError("Voter has no votes left")
		elif not self.is_clickable():  # module must be set-up
			raise RuntimeError("This module is not set up")

	def _update_clicks(self, clicker):
		"""Updates clicks for both the clicker and the module."""
		self.clicks_since_last_harvest += 1
		self.total_clicks += 1
		self.save()
		if clicker.profile.is_networker: return
		clicker.profile.available_votes -= 1
		clicker.profile.save()

	def get_settings_classes(self):
		"""Get the save data classes for this module."""
		return module_settings_classes[self.item.module_info.editor_type]

	def get_yield_item_id(self):
		"""Get the id of the item this module yields."""
		return ModuleHarvestYield.objects.get(item_id=self.item_id).yield_item_id

	def calc_yield_qty(self):
		"""Calculate the yield of this module."""
		return self._calc_yield_info()[0]

	def handle_trade(self, clicker):
		trade = self.setup_trade
		assert_has_item(clicker, trade.request_item.id, trade.request_qty)
		remove_inv_item(clicker, trade.request_item.id, trade.request_qty)
		add_inv_item(self.owner, trade.request_item.id, trade.request_qty)
		add_inv_item(clicker, trade.give_item.id, trade.give_qty)
		self.is_setup = False
		self.save()

	def handle_guest_yield(self, clicker):
		guest_yield = self._get_yield(self.item.moduleguestyields.all())
		if guest_yield is not None:
			guest_yield.on_click(self, clicker)
			if guest_yield.should_yield(self):
				return guest_yield

	def click(self, clicker):
		"""Updates clicks and distributes relevant rewards."""
		self._validate_click(clicker)

		# Handle most click handlers
		self.did_guest_win = random.choice([True, False])
		for model in CLICK_HANDLERS:
			for handler in model.objects.filter(module_item_id=self.item_id):
				handler.on_click(self, clicker)

		# Handle trades separately
		if ModuleSetupTrade in self.get_settings_classes():  # handle trades
			self.handle_trade(clicker)

		# Handle guest yields separately
		outcome = self.item.module_info.click_outcome
		result = None  # we return the guest yield to the UI
		if (outcome != ModuleOutcome.ARCADE):
			result = self.handle_guest_yield(clicker)

		# Update information about the module
		self._update_clicks(clicker)
		if self.is_setup and self.did_guest_win and outcome != ModuleOutcome.NUM_CLICKS:
			# Tear down the module if the guest won
			self.is_setup = False
			self.save()

		# For pseudo-networkers, have them click the user back
		if self.owner.profile.is_networker and self.owner.profile.is_pseudo:
			self.click_back(clicker)

		return result

	def click_back(self, clicker):
		# A pseudo-networker is a special networker added to re-balance the game
		# If you click a pseudo-networker's module, they will click yours back.
		# If you have several, they will keep clicking until one succeeds.
		if clicker.profile.is_networker: return  # only click back humans
		for human_module in clicker.modules.filter(item=self.item):
			try:
				human_module.click(self.owner)
				break
			except:
				continue

	def add_to_harvest(self, qty):
		self.yield_since_last_harvest += qty
		self.save()

	def grant_arcade_prize(self, clicker):
		all_prizes = self.item.moduleguestyields.all()
		prize = self._get_yield(all_prizes)
		add_inv_item(clicker, prize.item_id, prize.qty)
		return prize

	def harvest(self):
		"""
		Harvest the module.
		Place the yielded items into the owner's inventory, and update time and click counts.
		If the module was set up, the set up item will be lost at this point.
		"""
		harvest_qty, time_remainder, click_remainder = self._calc_yield_info()
		add_inv_item(self.owner, self.get_yield_item_id(), qty=harvest_qty)
		self.yield_since_last_harvest = 0
		self.last_harvest_time = now() - time_remainder
		self.clicks_since_last_harvest = click_remainder
		if self.is_setup: self.is_setup = False  # will automatically be fixed if not _needs_setup
		if ModuleSetupFriendShare in self.get_settings_classes():
			add_inv_item(self.setup_friend_share.friend, self.get_yield_item_id(), qty=harvest_qty)
		if ModuleSetupTrioPerformance in self.get_settings_classes():
			add_inv_item(self.setup_group_performance.friend_0, self.get_yield_item_id(), qty=harvest_qty)
			add_inv_item(self.setup_group_performance.friend_1, self.get_yield_item_id(), qty=harvest_qty)
		if ModuleSetupGroupPerformance in self.get_settings_classes():
			add_inv_item(self.setup_group_performance.friend_0, self.get_yield_item_id(), qty=harvest_qty)
			add_inv_item(self.setup_group_performance.friend_1, self.get_yield_item_id(), qty=harvest_qty)
			add_inv_item(self.setup_group_performance.friend_2, self.get_yield_item_id(), qty=harvest_qty)
		self.save()

	def is_clickable(self):
		"""Returns True if the owner set up this module, or it doesn't need setup."""
		# self.is_setup = None means it doesn't need setup, so we explicitly check for False.
		return self.owner.profile.is_networker or self.is_setup is not False

	def setup(self):
		"""
		Set up the module with items.

		No-op if the module is already setup, raises a RuntimeError if it cannot be setup.
		Raise RuntimeError if the owner doesn't have the required items in their inventory.
		"""
		if self.is_setup:
			return
		if not self._needs_setup():
			raise RuntimeError("Module is not setupable.")
		if ModuleSetupTrade in self.get_settings_classes():
			trade = self.setup_trade
			remove_inv_item(self.owner, trade.give_item_id, trade.give_qty)
		else:
			costs = ModuleSetupCost.objects.filter(module_item_id=self.item_id)
			for cost in costs:
				remove_inv_item(self.owner, cost.item_id, cost.qty)
		self.is_setup = True
		self.last_harvest_time = now()
		self.save()

	def teardown(self):
		"""Remove the set up items, raising an error if it's not setup."""
		if not self.is_setup:
			return
		if ModuleSetupTrade in self.get_settings_classes():
			trade = self.setup_trade
			add_inv_item(self.owner, trade.give_item_id, trade.give_qty)
		else:
			for cost in ModuleSetupCost.objects.filter(module_item_id=self.item_id):
				add_inv_item(self.owner, cost.item_id, cost.qty)
		self.is_setup = False
		self.save()

from .module_settings import ModuleSaveGeneric, ModuleSaveNetworkerPic, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupGroupPerformance, ModuleSetupTrade, ModuleSetupTrioPerformance
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
	ModuleEditorType.NETWORKER_PIC: (ModuleSaveNetworkerPic,),
	ModuleEditorType.NETWORKER_TEXT: (ModuleSaveGeneric, ModuleSaveNetworkerText),
	ModuleEditorType.NETWORKER_TRADE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.PLASTIC_PELLET_INDUCTOR: (ModuleSaveUGC,),
	ModuleEditorType.ROCKET_GAME: (ModuleSaveSticker, ModuleSaveRocketGame),
	ModuleEditorType.SOUNDTRACK: (ModuleSaveGeneric, ModuleSaveSoundtrack),
	ModuleEditorType.STICKER: (ModuleSaveSticker,),
	ModuleEditorType.STICKER_SHOPPE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.TRADE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.TRIO_PERFORMANCE: (ModuleSaveGeneric, ModuleSetupTrioPerformance),
	None: (),
}
