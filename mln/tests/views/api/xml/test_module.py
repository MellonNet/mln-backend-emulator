from mln.models.static import *
from mln.models.dynamic.module_settings import ModuleSaveGeneric
from mln.services.inventory import add_inv_item
from mln.tests.models.test_module import arcade_module, harvestable_module, has_harvestable_module, has_setupable_module, has_setup_cost, setup_setupable_module, setupable_module
from mln.tests.models.test_profile import one_user, two_users
from mln.tests.models.test_static import color
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.views.api.xml.handler_testcase import req_resp

@cls_setup
def background_item(cls):
	cls.BACKGROUND_ID = ItemInfo.objects.create(name="Background", type=ItemType.BACKGROUND).id

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
	module = self.other_user.modules.create(item_id=self.SETUPABLE_MODULE_ID, pos_x=0, pos_y=1)
	add_inv_item(self.other_user, self.SETUP_COST.item_id, self.SETUP_COST.qty)
	module.setup()

@setup
@requires(setupable_module, one_user)
def user_has_execution_cost(self):
	add_inv_item(self.user, self.EXECUTION_COST.item_id, self.EXECUTION_COST.qty)

@cls_setup
def generic_module(cls):
	cls.GENERIC_MODULE_ID = ItemInfo.objects.create(name="Generic Module", type=ItemType.MODULE).id
	ModuleInfo.objects.create(item_id=cls.GENERIC_MODULE_ID, is_executable=False, editor_type=ModuleEditorType.GENERIC)

@setup
@requires(generic_module, one_user)
def has_generic_module(self):
	self.module = self.user.modules.create(item_id=self.GENERIC_MODULE_ID, pos_x=0, pos_y=0)

@cls_setup
def module_skin(cls):
	cls.MODULE_SKIN_ID = ModuleSkin.objects.create(name="Module Skin").id

@setup
@requires(module_skin, color, has_generic_module)
def configured_generic_module(self):
	ModuleSaveGeneric.objects.create(module=self.module, skin_id=self.MODULE_SKIN_ID, color_id=self.COLOR_ID)

class GetModuleBgs(TestCase, metaclass=req_resp):
	SETUP = background_item, one_user
	DIR = "module"
	TESTS = "get_module_bgs",

# --- Not yet implemented ---
# class ModuleCollectWinnings(TestCase, metaclass=req_resp):
# 	SETUP = other_user_has_arcade_module,
# 	DIR = "module"
# 	TESTS = "module_collect_winnings_not_won", "module_collect_winnings_won",

# func = ModuleCollectWinnings.test_module_collect_winnings_won

class ModuleDetails(TestCase, metaclass=req_resp):
	SETUP = configured_generic_module,
	DIR = "module"
	TESTS = "module_details",

# TODO: This test was written before randomness was introduced,
# 	and the concept of is_clickable vs is_setup. It needs to be rewritten
# class ModuleExecute(TestCase, metaclass=req_resp):
# 	SETUP = other_user_has_setupable_module, user_has_execution_cost
# 	DIR = "module"
# 	TESTS = "module_execute",

class ModuleHarvest(TestCase, metaclass=req_resp):
	SETUP = has_harvestable_module,
	DIR = "module"
	VOID_TESTS = "module_harvest",

class ModuleSaveSettings(TestCase, metaclass=req_resp):
	SETUP = module_skin, color, has_generic_module,
	DIR = "module"
	TESTS = "module_save_settings",

class ModuleSetup(TestCase, metaclass=req_resp):
	SETUP = has_setup_cost, has_setupable_module
	DIR = "module"
	VOID_TESTS = "module_setup",

class ModuleTeardown(TestCase, metaclass=req_resp):
	SETUP = setup_setupable_module,
	DIR = "module"
	VOID_TESTS = "module_teardown",

class ModuleVote(TestCase, metaclass=req_resp):
	SETUP = other_user_has_harvestable_module,
	DIR = "module"
	TESTS = "module_vote",
