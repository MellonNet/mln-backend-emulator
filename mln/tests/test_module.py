from datetime import timedelta
from unittest.mock import patch

from mln.models.static import ArcadePrize, ItemInfo, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleYieldInfo
from mln.tests.setup_testcase import requires, setup, TestCase
from mln.tests.test_profile import one_user, two_users

@setup
@requires(one_user)
def flower_module(self):
	self.module = self.user.modules.create(item=ItemInfo.objects.get(name="Flower Patch Module"), pos_x=0, pos_y=0)

@setup
@requires(one_user)
def farm_module(self):
	self.module = self.user.modules.create(item=ItemInfo.objects.get(name="Farm Pet Module, Rank 1"), pos_x=0, pos_y=0)

@setup
@requires(farm_module)
def setup_farm_module(self):
	self.module.is_setup = True

@setup
@requires(one_user)
def arcade_module(self):
	self.module = self.user.modules.create(item=ItemInfo.objects.get(name="Delivery Arcade Game"), pos_x=0, pos_y=0)

class HarvestTest(TestCase):
	SETUP = flower_module,

	def test_get_info(self):
		self.assertEqual(self.module.get_info(), ModuleInfo.objects.get(item_id=self.module.item_id))

	def test_calc_yield_qty_time(self):
		self.assertEqual(self.module.calc_yield_qty(), 0)
		self.module.last_harvest_time = self.module.last_harvest_time - timedelta(days=1)
		self.assertEqual(self.module.calc_yield_qty(), ModuleYieldInfo.objects.get(item_id=self.module.item_id).yield_per_day)

	def test_calc_yield_qty_clicks(self):
		clicks = 42
		self.assertEqual(self.module.calc_yield_qty(), 0)
		self.module.clicks_since_last_harvest = clicks
		self.assertEqual(self.module.calc_yield_qty(), clicks//ModuleYieldInfo.objects.get(item_id=self.module.item_id).clicks_per_yield)

	def test_calc_yield_qty_max(self):
		info = ModuleYieldInfo.objects.get(item_id=self.module.item_id)
		clicks = info.clicks_per_yield * info.max_yield * 10
		self.assertEqual(self.module.calc_yield_qty(), 0)
		self.module.clicks_since_last_harvest = clicks
		self.assertEqual(self.module.calc_yield_qty(), info.max_yield)

	def test_get_yield_item_id(self):
		self.assertEqual(self.module.get_yield_item_id(), ModuleYieldInfo.objects.get(item_id=self.module.item_id).yield_item_id)

	def test_harvest(self):
		clicks = 42
		now = self.module.last_harvest_time
		self.module.last_harvest_time = self.module.last_harvest_time - timedelta(hours=5)
		self.module.clicks_since_last_harvest = clicks
		with patch("mln.models.module.now", return_value=now):
			harvest_qty, time_remainder, click_remainder = self.module._calc_yield_info()
			self.module.harvest()
		self.assertTrue(self.user.inventory.filter(item_id=self.module.get_yield_item_id(), qty=harvest_qty).exists())
		self.assertEqual(self.module.last_harvest_time, now - time_remainder)
		self.assertEqual(self.module.clicks_since_last_harvest, click_remainder)
		self.assertFalse(self.module.is_setup)

class VoteExecuteTest(TestCase):
	SETUP = two_users, farm_module, setup_farm_module

	def test_vote_ok(self):
		av_votes = self.other_user.profile.available_votes
		self.module.vote(self.other_user)
		self.assertEqual(self.module.clicks_since_last_harvest, 1)
		self.assertEqual(self.module.total_clicks, 1)
		self.assertEqual(self.other_user.profile.available_votes, av_votes - 1)

	def test_vote_self(self):
		with self.assertRaises(ValueError):
			self.module.vote(self.user)

	def test_vote_no_votes_left(self):
		self.other_user.profile.available_votes = 0
		with self.assertRaises(RuntimeError):
			self.module.vote(self.other_user)

	def test_execute_no_items(self):
		with self.assertRaises(RuntimeError):
			self.module.execute(self.other_user)

	def test_execute_ok(self):
		for cost in ModuleExecutionCost.objects.filter(module_item_id=self.module.item_id):
			self.other_user.profile.add_inv_item(cost.item_id, cost.qty)
		self.module.execute(self.other_user)
		for cost in ModuleExecutionCost.objects.filter(module_item_id=self.module.item_id):
			self.assertFalse(self.other_user.inventory.filter(item_id=cost.item_id, qty=cost.qty).exists())

class SetupableTest(TestCase):
	SETUP = farm_module,

	def test_setup_no_items(self):
		with self.assertRaises(RuntimeError):
			self.module.setup()

	def test_setup_ok(self):
		costs = ModuleSetupCost.objects.filter(module_item_id=self.module.item_id)
		for cost in costs:
			self.user.profile.add_inv_item(cost.item_id, cost.qty)
		self.module.setup()
		for cost in costs:
			self.assertFalse(self.user.inventory.filter(item_id=cost.item_id).exists())
		self.assertTrue(self.module.is_setup)

	def test_setup_already_setup(self):
		self.module.is_setup = True
		costs = ModuleSetupCost.objects.filter(module_item_id=self.module.item_id)
		for cost in costs:
			self.user.profile.add_inv_item(cost.item_id, cost.qty)
		self.module.setup()
		for cost in costs:
			self.assertTrue(self.user.inventory.filter(item_id=cost.item_id, qty=cost.qty).exists())
		self.assertTrue(self.module.is_setup)

	def test_teardown_ok(self):
		self.module.is_setup = True
		self.module.teardown()
		costs = ModuleSetupCost.objects.filter(module_item_id=self.module.item_id)
		for cost in costs:
			self.assertTrue(self.user.inventory.filter(item_id=cost.item_id, qty=cost.qty).exists())
		self.assertFalse(self.module.is_setup)

	def test_teardown_not_setup(self):
		self.module.is_setup = False
		self.module.teardown()
		costs = ModuleSetupCost.objects.filter(module_item_id=self.module.item_id)
		for cost in costs:
			self.assertFalse(self.user.inventory.filter(item_id=cost.item_id).exists())
		self.assertFalse(self.module.is_setup)

class ArcadeTest(TestCase):
	SETUP = arcade_module, two_users

	def test_select_arcade_prize(self):
		with patch("random.randrange", return_value=0):
			self.module.select_arcade_prize(self.other_user)
		prize = ArcadePrize.objects.filter(module_item_id=self.module.item_id)[0]
		self.assertTrue(self.other_user.inventory.filter(item_id=prize.item_id, qty=prize.qty).exists())
