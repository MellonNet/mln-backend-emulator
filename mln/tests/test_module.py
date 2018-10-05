from datetime import timedelta
from unittest.mock import patch

from mln.models.static import ArcadePrize, ItemInfo, ItemType, ModuleEditorType, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleYieldInfo
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.test_profile import item, one_user, two_users

@cls_setup
@requires(item)
def harvestable_module(cls):
	cls.HARVESTABLE_MODULE_ID = ItemInfo.objects.create(name="Harvestable Module", type=ItemType.MODULE).id
	cls.MODULE_INFO = ModuleInfo.objects.create(item_id=cls.HARVESTABLE_MODULE_ID, is_executable=False, is_setupable=False, editor_type=ModuleEditorType.GENERIC)
	cls.MODULE_YIELD_INFO = ModuleYieldInfo.objects.create(item_id=cls.HARVESTABLE_MODULE_ID, yield_item_id=cls.ITEM_ID, max_yield=10, yield_per_day=5, clicks_per_yield=20)

@setup
@requires(harvestable_module, one_user)
def has_harvestable_module(self):
	self.h_module = self.user.modules.create(item_id=self.HARVESTABLE_MODULE_ID, pos_x=0, pos_y=0)

@setup
@requires(harvestable_module, one_user)
def has_harvestable_module_stack(self):
	self.user.profile.add_inv_item(self.HARVESTABLE_MODULE_ID)

@cls_setup
@requires(item)
def setupable_module(cls):
	cls.SETUPABLE_MODULE_ID = ItemInfo.objects.create(name="Setupable Module", type=ItemType.MODULE).id
	ModuleInfo.objects.create(item_id=cls.SETUPABLE_MODULE_ID, is_executable=True, is_setupable=True, editor_type=ModuleEditorType.GENERIC)
	cls.SETUP_COST = ModuleSetupCost.objects.create(module_item_id=cls.SETUPABLE_MODULE_ID, item_id=cls.ITEM_ID, qty=10)
	cls.EXECUTION_COST = ModuleExecutionCost.objects.create(module_item_id=cls.SETUPABLE_MODULE_ID, item_id=cls.ITEM_ID, qty=1)

@setup
@requires(setupable_module, one_user)
def has_setupable_module(self):
	self.s_module = self.user.modules.create(item_id=self.SETUPABLE_MODULE_ID, pos_x=0, pos_y=1)

@setup
@requires(setupable_module, one_user)
def has_setup_cost(self):
	self.user.profile.add_inv_item(self.SETUP_COST.item_id, self.SETUP_COST.qty)

@setup
@requires(setupable_module, one_user)
def has_execution_cost(self):
	self.other_user.profile.add_inv_item(self.EXECUTION_COST.item_id, self.EXECUTION_COST.qty)

@setup
@requires(has_setupable_module)
def setup_setupable_module(self):
	self.s_module.is_setup = True
	self.s_module.save()

@cls_setup
def arcade_module(cls):
	cls.ARCADE_MODULE_ID = ItemInfo.objects.create(name="Delivery Arcade Game", type=ItemType.MODULE).id
	cls.ARCADE_PRIZE_IDS = []
	for i in range(5):
		prize_id = ItemInfo.objects.create(name="Arcade Prize %i" % i, type=ItemType.ITEM).id
		ArcadePrize.objects.create(module_item_id=cls.ARCADE_MODULE_ID, item_id=prize_id, qty=i, success_rate=20)
		cls.ARCADE_PRIZE_IDS.append(prize_id)

@setup
@requires(arcade_module, one_user)
def has_arcade_module(self):
	self.a_module = self.user.modules.create(item_id=self.ARCADE_MODULE_ID, pos_x=0, pos_y=2)

class HarvestTest(TestCase):
	SETUP = has_harvestable_module,

	def test_get_info(self):
		self.assertEqual(self.h_module.get_info(), self.MODULE_INFO)

	def test_calc_yield_qty_time(self):
		self.assertEqual(self.h_module.calc_yield_qty(), 0)
		self.h_module.last_harvest_time = self.h_module.last_harvest_time - timedelta(days=1)
		self.assertEqual(self.h_module.calc_yield_qty(), self.MODULE_YIELD_INFO.yield_per_day)

	def test_calc_yield_qty_clicks(self):
		clicks = 42
		self.assertEqual(self.h_module.calc_yield_qty(), 0)
		self.h_module.clicks_since_last_harvest = clicks
		self.assertEqual(self.h_module.calc_yield_qty(), clicks//self.MODULE_YIELD_INFO.clicks_per_yield)

	def test_calc_yield_qty_max(self):
		info = self.MODULE_YIELD_INFO
		clicks = info.clicks_per_yield * info.max_yield * 10
		self.assertEqual(self.h_module.calc_yield_qty(), 0)
		self.h_module.clicks_since_last_harvest = clicks
		self.assertEqual(self.h_module.calc_yield_qty(), info.max_yield)

	def test_get_yield_item_id(self):
		self.assertEqual(self.h_module.get_yield_item_id(), self.MODULE_YIELD_INFO.yield_item_id)

	def test_harvest(self):
		clicks = 42
		now = self.h_module.last_harvest_time
		self.h_module.last_harvest_time = self.h_module.last_harvest_time - timedelta(hours=5)
		self.h_module.clicks_since_last_harvest = clicks
		with patch("mln.models.module.now", return_value=now):
			harvest_qty, time_remainder, click_remainder = self.h_module._calc_yield_info()
			self.h_module.harvest()
		self.assertTrue(self.user.inventory.filter(item_id=self.h_module.get_yield_item_id(), qty=harvest_qty).exists())
		self.assertEqual(self.h_module.last_harvest_time, now - time_remainder)
		self.assertEqual(self.h_module.clicks_since_last_harvest, click_remainder)
		self.assertFalse(self.h_module.is_setup)

class VoteExecuteTest(TestCase):
	SETUP = two_users, setup_setupable_module

	def test_vote_ok(self):
		av_votes = self.other_user.profile.available_votes
		self.s_module.vote(self.other_user)
		self.assertEqual(self.s_module.clicks_since_last_harvest, 1)
		self.assertEqual(self.s_module.total_clicks, 1)
		self.assertEqual(self.other_user.profile.available_votes, av_votes - 1)

	def test_vote_self(self):
		with self.assertRaises(ValueError):
			self.s_module.vote(self.user)

	def test_vote_no_votes_left(self):
		self.other_user.profile.available_votes = 0
		with self.assertRaises(RuntimeError):
			self.s_module.vote(self.other_user)

	def test_execute_no_items(self):
		with self.assertRaises(RuntimeError):
			self.s_module.execute(self.other_user)

class ExecuteOkTest(TestCase):
	SETUP = two_users, setup_setupable_module, has_execution_cost

	def test_execute_ok(self):
		self.s_module.execute(self.other_user)
		self.assertFalse(self.other_user.inventory.filter(item_id=self.EXECUTION_COST.item_id, qty=self.EXECUTION_COST.qty).exists())

class SetupableTest(TestCase):
	SETUP = has_setupable_module,

	def test_setup_no_items(self):
		with self.assertRaises(RuntimeError):
			self.s_module.setup()

	def test_setup_already_setup(self):
		self.s_module.is_setup = True
		costs = ModuleSetupCost.objects.filter(module_item_id=self.s_module.item_id)
		for cost in costs:
			self.user.profile.add_inv_item(cost.item_id, cost.qty)
		self.s_module.setup()
		for cost in costs:
			self.assertTrue(self.user.inventory.filter(item_id=cost.item_id, qty=cost.qty).exists())
		self.assertTrue(self.s_module.is_setup)

	def test_teardown_ok(self):
		self.s_module.is_setup = True
		self.s_module.teardown()
		costs = ModuleSetupCost.objects.filter(module_item_id=self.s_module.item_id)
		for cost in costs:
			self.assertTrue(self.user.inventory.filter(item_id=cost.item_id, qty=cost.qty).exists())
		self.assertFalse(self.s_module.is_setup)

	def test_teardown_not_setup(self):
		self.s_module.is_setup = False
		self.s_module.teardown()
		costs = ModuleSetupCost.objects.filter(module_item_id=self.s_module.item_id)
		for cost in costs:
			self.assertFalse(self.user.inventory.filter(item_id=cost.item_id).exists())
		self.assertFalse(self.s_module.is_setup)

class SetupOkTest(TestCase):
	SETUP = has_setup_cost, has_setupable_module

	def test_setup_ok(self):
		self.s_module.setup()
		self.assertFalse(self.user.inventory.filter(item_id=self.SETUP_COST.item_id).exists())
		self.assertTrue(self.s_module.is_setup)

class ArcadeTest(TestCase):
	SETUP = has_arcade_module, two_users

	def test_select_arcade_prize(self):
		with patch("random.randrange", return_value=0):
			self.a_module.select_arcade_prize(self.other_user)
		prize = ArcadePrize.objects.filter(module_item_id=self.a_module.item_id)[0]
		self.assertTrue(self.other_user.inventory.filter(item_id=prize.item_id, qty=prize.qty).exists())
