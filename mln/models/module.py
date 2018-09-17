"""The model for modules. Module settings are in their own files."""
import random

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

from .dynamic import DAY, get_or_none
from .static import ArcadePrize, ItemInfo, ItemType, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleYieldInfo

class Module(models.Model):
	"""
	A module instance on a user's page.
	This does not represent a stack of modules in the user's inventory, for that, see InventoryStack.
	"""
	item = models.ForeignKey(ItemInfo, related_name="+", on_delete=models.CASCADE, limit_choices_to={"type": ItemType.MODULE})
	pos_x = models.PositiveSmallIntegerField()
	pos_y = models.PositiveSmallIntegerField()
	last_harvest_time = models.DateTimeField(default=now)
	clicks_since_last_harvest = models.PositiveSmallIntegerField(default=0)
	total_clicks = models.PositiveIntegerField(default=0)
	is_setup = models.BooleanField(default=False) # this is actually only relevant for some modules, refactor?
	owner = models.ForeignKey(User, related_name="modules", on_delete=models.CASCADE)

	def __str__(self):
		return "%s's %s at pos (%i, %i), %i clicks" % (self.owner, self.item.name, self.pos_x, self.pos_y, self.total_clicks)

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
				if not self.owner.inventory.filter(item_id=cost.item_id, qty__gte=cost.qty).exists():
					raise RuntimeError("Owner doesn't have setup requirement %s in inventory" % cost)
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
			executer.profile.remove_inv_item(trade.request_item, trade.request_qty)
			executer.profile.add_inv_item(trade.give_item_id, trade.give_qty)
			self.owner.profile.add_inv_item(trade.request_item, trade.request_qty)
			# give item was already taken from owner at setup
		else:
			costs = ModuleExecutionCost.objects.filter(module_item_id=self.item_id)
			for cost in costs:
				if not executer.inventory.filter(item_id=cost.item_id, qty__gte=cost.qty).exists():
					raise RuntimeError("Executer doesn't have execution cost %s in inventory" % cost)
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
		href = info.href_editor
		href = href[href.rindex("/")+1:href.rindex(".")]
		if href in module_settings_classes:
			return module_settings_classes[href]
		print("warning: no classes defined for", href)
		return ()


from .module_settings import ModuleSaveGeneric, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupGroupPerformance, ModuleSetupTrade, ModuleSetupTrioPerformance
from .module_settings_arcade import ModuleSaveConcertArcade, ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade

"""Settings class registry. This links module types to settings classes."""
module_settings_classes = {
	"upload6BE2047F-A1E7-46FE-ABE9-CD910C6EF59D": (ModuleSaveGeneric, ModuleSaveUGC),
	"uploadE79A5782-F4CC-4FA6-B71B-5266E2830236": (ModuleSaveUGC,),
	"upload5F35F258-650A-46E6-A4F3-07C4823F51EA": (ModuleSaveGeneric,),
	"upload94145C71-2215-40F4-BC55-705F8CA24ACA": (ModuleSaveGeneric, ModuleSaveUGC),
	"upload6FE45D31-426C-41DC-96F0-04C16BDAC640": (ModuleSaveUGC,),
	"upload5E54C1F7-9D69-4089-A28B-C9A6054C2482": (ModuleSaveGeneric, ModuleSetupFriendShare),
	"uploadBD27CDD3-01AB-4A14-B065-44AD7295987F": (ModuleSaveGeneric, ModuleSetupGroupPerformance),
	"upload2ADB5931-F7EE-4363-9AFB-EBA8E45C6FB8": (ModuleSaveGeneric, ModuleSetupTrade),
	"uploadC85FF476-57A7-41EE-BA1A-45D259F438A8": (ModuleSaveGeneric, ModuleSaveNetworkerText),
	"upload66F5B629-AEB6-4C04-B56C-BC1BCA22ABF5": (ModuleSaveGeneric, ModuleSetupTrade),
	"upload5CD17986-C326-4A56-9094-552F275D5906": (ModuleSaveGeneric, ModuleSaveSoundtrack),
	"upload617A0D10-FA99-42AA-8B44-6534997F8819": (ModuleSaveSticker,),
	"upload28814700-1EEA-458C-A494-6C4797739455": (ModuleSetupTrade,),
	"uploadB58AC317-A0A2-41C4-8AA7-2086AB69CE9A": (ModuleSaveGeneric, ModuleSetupTrade),
	"uploadF10B502A-8D24-43E3-BA33-84C183B5D857": (ModuleSaveGeneric, ModuleSetupTrioPerformance),
	"uploadD668BCBE-4B58-406B-91C8-3C09AC4216DF": (ModuleSaveUGC,),
	"upload3B10831D-FEBE-4C44-B964-6D69B49EA1C6": (ModuleSaveSticker, ModuleSaveRocketGame),
	"download124C900AD0613F3B0E8683473AC6B267": (ModuleSaveConcertArcade,),
	"download16F9FFF4A1719FF27AA4E4BD59ACAC27": (ModuleSaveHopArcade,),
	"download3C08891ADDFAF741ECF73F38FB40B2A3": (ModuleSaveConcertArcade,),
	"download6308BE1BFE39A4E7A3ADC4D112807016": (ModuleSaveDestructoidArcade,),
	"download65E88EEE1750F1FF25361D8A52651BF1": (ModuleSaveDestructoidArcade,),
	"download7BBDE1968863AF36A4723D79CEBE817E": (ModuleSaveDeliveryArcade,),
	"download8D2D8E39CFEEF2BE409F2557F48F810C": (ModuleSaveConcertArcade,),
}
