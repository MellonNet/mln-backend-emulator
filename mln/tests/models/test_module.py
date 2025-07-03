from datetime import timedelta
from django.core.exceptions import ValidationError
from unittest.mock import patch

from mln.models.dynamic.module_settings import ModuleSetupTrade
from mln.models.static import *
from mln.models.static.module_handlers import *
from mln.services.inventory import add_inv_item
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.models.dupe_testcase import DupeTest
from mln.tests.models.test_profile import one_user, other_user_has_item, two_users, user_has_item
from mln.tests.models.test_static import item

@cls_setup
@requires(item)
def harvestable_module(cls):
	cls.HARVESTABLE_MODULE_ID = ItemInfo.objects.create(name="Harvestable Module", type=ItemType.MODULE).id
	cls.MODULE_INFO = ModuleInfo.objects.create(item_id=cls.HARVESTABLE_MODULE_ID, is_executable=False, editor_type=ModuleEditorType.GENERIC)
	cls.MODULE_YIELD_INFO = ModuleHarvestYield.objects.create(item_id=cls.HARVESTABLE_MODULE_ID, yield_item_id=cls.ITEM_ID, max_yield=10, yield_per_day=5, clicks_per_yield=20)

@setup
@requires(harvestable_module, one_user)
def has_harvestable_module(self):
	self.h_module = self.user.modules.create(item_id=self.HARVESTABLE_MODULE_ID, pos_x=0, pos_y=0)

@setup
@requires(harvestable_module, one_user)
def has_harvestable_module_stack(self):
	add_inv_item(self.user, self.HARVESTABLE_MODULE_ID)

@cls_setup
@requires(item)
def setupable_module_item(cls):
	cls.SETUPABLE_MODULE_ID = ItemInfo.objects.create(name="Setupable Module", type=ItemType.MODULE).id
	ModuleInfo.objects.create(item_id=cls.SETUPABLE_MODULE_ID, is_executable=True, editor_type=ModuleEditorType.GENERIC)


@cls_setup
@requires(setupable_module_item)
def module_setup_cost(cls):
	cls.SETUP_COST = ModuleSetupCost.objects.create(module_item_id=cls.SETUPABLE_MODULE_ID, item_id=cls.ITEM_ID, qty=10)

@cls_setup
@requires(setupable_module_item)
def module_exec_cost(cls):
	cls.EXECUTION_COST = ModuleExecutionCost.objects.create(module_item_id=cls.SETUPABLE_MODULE_ID, item_id=cls.ITEM_ID, qty=1)


@cls_setup
@requires(setupable_module_item, module_setup_cost, module_exec_cost)
def setupable_module(cls):
	pass

@setup
@requires(setupable_module, one_user)
def has_setupable_module(self):
	self.s_module = self.user.modules.create(item_id=self.SETUPABLE_MODULE_ID, pos_x=0, pos_y=1)

@setup
@requires(setupable_module, one_user)
def has_setup_cost(self):
	add_inv_item(self.user, self.SETUP_COST.item_id, self.SETUP_COST.qty)

@setup
@requires(setupable_module, one_user)
def has_execution_cost(self):
	add_inv_item(self.other_user, self.EXECUTION_COST.item_id, self.EXECUTION_COST.qty)

@setup
@requires(has_setupable_module)
def setup_setupable_module(self):
	self.s_module.is_setup = True
	self.s_module.save()

@cls_setup
def trade_module(cls):
	cls.TRADE_MODULE_ID = ItemInfo.objects.create(name="Trade Module", type=ItemType.MODULE).id
	ModuleInfo.objects.create(item_id=cls.TRADE_MODULE_ID, is_executable=True, editor_type=ModuleEditorType.TRADE)

@setup
@requires(item, trade_module, one_user)
def has_trade_module(self):
	self.t_module = self.user.modules.create(item_id=self.TRADE_MODULE_ID, pos_x=0, pos_y=1)

@setup
@requires(has_trade_module)
def configured_trade_module(self):
	ModuleSetupTrade.objects.create(module=self.t_module, give_item_id=self.ITEM_ID, give_qty=1, request_item_id=self.ITEM_ID, request_qty=1)

@setup
@requires(configured_trade_module)
def setup_trade_module(self):
	self.t_module.is_setup = True
	self.t_module.save()

@cls_setup
def arcade_module(cls):
	cls.ARCADE_MODULE_ID = ItemInfo.objects.create(name="Delivery Arcade Game", type=ItemType.MODULE).id
	ModuleInfo.objects.create(item_id=cls.ARCADE_MODULE_ID, is_executable=True, editor_type=ModuleEditorType.HOP_ARCADE)

@setup
@requires(arcade_module, one_user)
def has_arcade_module(self):
	self.a_module = self.user.modules.create(item_id=self.ARCADE_MODULE_ID, pos_x=0, pos_y=2)

class DuplicateModule(DupeTest):
	SETUP = has_harvestable_module,

class DuplicateModuleSetupCost(DupeTest):
	SETUP = module_setup_cost,

class DuplicateModuleExecCost(DupeTest):
	SETUP = module_exec_cost,

class Harvest(TestCase):
	SETUP = has_harvestable_module,

	def test_get_info(self):
		self.assertEqual(self.h_module.item.module_info, self.MODULE_INFO)

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

class Execute(TestCase):
	SETUP = two_users, setup_setupable_module

	def test_vote_self(self):
		with self.assertRaises(ValueError):
			self.s_module.click(self.user)

	def test_vote_no_votes_left(self):
		self.other_user.profile.available_votes = 0
		with self.assertRaises(RuntimeError):
			self.s_module.click(self.other_user)

	def test_execute_no_items(self):
		with self.assertRaises(ValidationError):
			self.s_module.click(self.other_user)

class Execute_Ok(TestCase):
	SETUP = two_users, setup_setupable_module, has_execution_cost

	def test(self):
		self.s_module.click(self.other_user)
		self.assertFalse(self.other_user.inventory.filter(item_id=self.EXECUTION_COST.item_id, qty=self.EXECUTION_COST.qty).exists())

	def test_ok(self):
		av_votes = self.other_user.profile.available_votes
		self.s_module.click(self.other_user)
		self.assertEqual(self.s_module.clicks_since_last_harvest, 1)
		self.assertEqual(self.s_module.total_clicks, 1)
		self.assertEqual(self.other_user.profile.available_votes, av_votes - 1)

class Setupable(TestCase):
	SETUP = has_setupable_module,

	def test_setup_no_items(self):
		with self.assertRaises(RuntimeError):
			self.s_module.setup()

	def test_setup_already_setup(self):
		self.s_module.is_setup = True
		costs = ModuleSetupCost.objects.filter(module_item_id=self.s_module.item_id)
		for cost in costs:
			add_inv_item(self.user, cost.item_id, cost.qty)
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

class Setup_HasItem(TestCase):
	SETUP = has_setup_cost, has_setupable_module

	def test(self):
		self.s_module.setup()
		self.assertFalse(self.user.inventory.filter(item_id=self.SETUP_COST.item_id).exists())
		self.assertTrue(self.s_module.is_setup)

class Trade_Setup_NoItem(TestCase):
	SETUP = configured_trade_module,

	def test(self):
		with self.assertRaises(RuntimeError):
			self.t_module.setup()

class Trade_Setup_HasItem(TestCase):
	SETUP = configured_trade_module, user_has_item

	def test(self):
		self.t_module.setup()
		self.assertFalse(self.user.inventory.filter(item_id=self.ITEM_ID).exists())
		self.assertTrue(self.t_module.is_setup)

class Trade_Teardown(TestCase):
	SETUP = setup_trade_module,

	def test(self):
		self.t_module.teardown()
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=1).exists())
		self.assertFalse(self.t_module.is_setup)

class Trade_Execute_NoItem(TestCase):
	SETUP = setup_trade_module, two_users

	def test(self):
		with self.assertRaises(ValidationError):
			self.t_module.click(self.other_user)

class Trade_Execute_HasItem(TestCase):
	SETUP = setup_trade_module, two_users, other_user_has_item

	def test(self):
		self.t_module.click(self.other_user)
		self.assertTrue(self.other_user.inventory.filter(item_id=self.ITEM_ID, qty=1).exists())
		self.assertFalse(self.t_module.is_setup)
