from mln.tests.models.test_profile import one_user, statements
from mln.tests.services.test_misc import has_item_blueprint, has_module, has_requirement
from mln.tests.setup_testcase import TestCase
from mln.tests.views.api.xml.handler_testcase import req_resp

class BlueprintUse(TestCase, metaclass=req_resp):
	SETUP = has_item_blueprint, has_requirement
	DIR = "misc"
	VOID_TESTS = "blueprint_use",

class InventoryModuleGet(TestCase, metaclass=req_resp):
	SETUP = has_module,
	DIR = "misc"
	TESTS = "inventory_module_get",

class Avatar(TestCase, metaclass=req_resp):
	SETUP = one_user,
	DIR = "misc"
	TESTS = "user_get_my_avatar",
	VOID_TESTS = "user_save_my_avatar",

class Statements(TestCase, metaclass=req_resp):
	SETUP = one_user, statements
	DIR = "misc"
	VOID_TESTS = "user_save_my_statements",
