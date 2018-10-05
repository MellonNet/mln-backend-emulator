from unittest.mock import patch

from mln.models.static import ItemInfo, ItemType
from mln.tests.views.api.xml.handler_testcase import req_resp
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.models.test_module import arcade_module, harvestable_module, has_harvestable_module, has_setupable_module, has_setup_cost, setup_setupable_module, setupable_module
from mln.tests.models.test_profile import one_user, two_users

@cls_setup
def background_item(cls):
	ItemInfo.objects.create(name="Background", type=ItemType.BACKGROUND)

@setup
@requires(arcade_module, two_users)
def other_user_has_arcade_module(self):
	self.other_user.modules.create(item_id=self.ARCADE_MODULE_ID, pos_x=0, pos_y=2)

@setup
@requires(harvestable_module, two_users)
def other_user_has_harvestable_module(self):
	self.other_user.modules.create(item_id=self.HARVESTABLE_MODULE_ID, pos_x=0, pos_y=0)

@setup
@requires(setupable_module, two_users)
def other_user_has_setupable_module(self):
	self.other_user.modules.create(item_id=self.SETUPABLE_MODULE_ID, pos_x=0, pos_y=1)

@setup
@requires(setupable_module, one_user)
def user_has_execution_cost(self):
	self.user.profile.add_inv_item(self.EXECUTION_COST.item_id, self.EXECUTION_COST.qty)

class GetModuleBgsTest(TestCase, metaclass=req_resp):
	SETUP = background_item, one_user
	DIR = "module"
	TESTS = "get_module_bgs",

class ModuleCollectWinningsTest(TestCase, metaclass=req_resp):
	SETUP = other_user_has_arcade_module,
	DIR = "module"
	TESTS = "module_collect_winnings_not_won", "module_collect_winnings_won",

func = ModuleCollectWinningsTest.test_module_collect_winnings_won

def patched(*args, **kwargs):
	with patch("random.randrange", return_value=0):
		func(*args, **kwargs)

ModuleCollectWinningsTest.test_module_collect_winnings_won = patched

class ModuleExecuteTest(TestCase, metaclass=req_resp):
	SETUP = other_user_has_setupable_module, user_has_execution_cost
	DIR = "module"
	TESTS = "module_execute",

class ModuleHarvestTest(TestCase, metaclass=req_resp):
	SETUP = has_harvestable_module,
	DIR = "module"
	VOID_TESTS = "module_harvest",

class ModuleSetupTest(TestCase, metaclass=req_resp):
	SETUP = has_setup_cost, has_setupable_module
	DIR = "module"
	VOID_TESTS = "module_setup",

class ModuleTeardownTest(TestCase, metaclass=req_resp):
	SETUP = setup_setupable_module,
	DIR = "module"
	VOID_TESTS = "module_teardown",

class ModuleVoteTest(TestCase, metaclass=req_resp):
	SETUP = other_user_has_harvestable_module,
	DIR = "module"
	TESTS = "module_vote",
