from django.core.exceptions import ValidationError

from mln.models.static import ItemInfo, ItemType
from mln.services.inventory import add_inv_item, assert_has_item
from mln.services.misc import inventory_module_get, use_blueprint
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.models.test_profile import networker, one_user, user_has_item
from mln.tests.models.test_static import masterpiece_blueprint_req, blueprint_req, item, masterpiece

@cls_setup
def module(cls):
	cls.MODULE_ITEM_ID = ItemInfo.objects.create(name="Module Item", type=ItemType.MODULE).id

@cls_setup
def module_2(cls):
	cls.MODULE_ITEM_2_ID = ItemInfo.objects.create(name="Module Item 2", type=ItemType.MODULE).id

@setup
@requires(module, one_user)
def has_module(self):
	add_inv_item(self.user, self.MODULE_ITEM_ID)

@setup
@requires(masterpiece, one_user)
def has_masterpiece(self):
	add_inv_item(self.user, self.MASTERPIECE_ITEM_ID)

@setup
@requires(blueprint_req, one_user)
def has_item_blueprint(self):
	add_inv_item(self.user, self.BLUEPRINT_ID)

@setup
@requires(masterpiece_blueprint_req, one_user)
def has_masterpiece_blueprint(self):
	add_inv_item(self.user, self.MASTERPIECE_BLUEPRINT_ID)

@setup
@requires(masterpiece_blueprint_req, one_user)
def has_masterpiece_requirement(self):
	add_inv_item(self.user, self.MASTERPIECE_REQUIREMENT_ID)

@setup
@requires(blueprint_req, one_user)
def has_requirement(self):
	add_inv_item(self.user, self.REQUIREMENT_ID)

class InventoryModuleGet_UserNoModules(TestCase):
	SETUP = module, one_user

	def test(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 0)

class InventoryModuleGet_UserHasModule(TestCase):
	SETUP = has_module,

	def test(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 1)
		self.assertIn((self.MODULE_ITEM_ID, 1), module_stacks)

class InventoryModuleGet_NetworkerNoModules(TestCase):
	SETUP = module, module_2, networker

	def test(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 2)
		self.assertIn((self.MODULE_ITEM_ID, 1), module_stacks)
		self.assertIn((self.MODULE_ITEM_2_ID, 1), module_stacks)

class InventoryModuleGet_NetworkerHasModule(TestCase):
	SETUP = has_module, module_2, networker

	def test(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 2)
		self.assertIn((self.MODULE_ITEM_ID, 1), module_stacks)
		self.assertIn((self.MODULE_ITEM_2_ID, 1), module_stacks)

class UseBlueprint_NoBlueprint(TestCase):
	SETUP = blueprint_req, one_user

	def test(self):
		with self.assertRaises(ValidationError):
			use_blueprint(self.user, self.BLUEPRINT_ID)

class UseBlueprint_RequirementsNotMet(TestCase):
	SETUP = has_item_blueprint,

	def test(self):
		with self.assertRaises(RuntimeError):
			use_blueprint(self.user, self.BLUEPRINT_ID)

class UseBlueprint_Ok(TestCase):
	SETUP = has_item_blueprint, has_requirement

	def test(self):
		use_blueprint(self.user, self.BLUEPRINT_ID)
		self.assertFalse(self.user.inventory.filter(item_id=self.REQUIREMENT_ID).exists())
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=1).exists())

class CraftMasterpiece_Ok(TestCase):
	SETUP = has_masterpiece_blueprint, has_masterpiece_requirement
	
	def test(self):
		use_blueprint(self.user, self.MASTERPIECE_BLUEPRINT_ID)
		self.assertFalse(self.user.inventory.filter(item_id=self.MASTERPIECE_REQUIREMENT_ID).exists())
		self.assertTrue(self.user.inventory.filter(item_id=self.MASTERPIECE_ITEM_ID, qty=1).exists())
		self.assertEqual(self.user.profile.rank, 1)

class CraftMasterpiece_Dupe(TestCase):
	SETUP = has_masterpiece_blueprint, has_masterpiece_requirement, has_masterpiece
	
	def test(self):
		use_blueprint(self.user, self.MASTERPIECE_BLUEPRINT_ID)
		self.assertFalse(self.user.inventory.filter(item_id=self.MASTERPIECE_REQUIREMENT_ID).exists())
		self.assertFalse(self.user.inventory.filter(item_id=self.MASTERPIECE_ITEM_ID, qty=2).exists())
		self.assertEqual(self.user.profile.rank, 0)

class AssertHasItem_NoItem(TestCase):
	SETUP = item, one_user

	def test(self):
		with self.assertRaises(ValidationError):
			assert_has_item(self.user, self.ITEM_ID)

class AssertHasItem_HasItem(TestCase):
	SETUP = user_has_item,

	def test(self):
		self.assertIsNone(assert_has_item(self.user, self.ITEM_ID))

class AssertHasItem_NoItem_Networker(TestCase):
	SETUP = item, networker

	def test(self):
		self.assertIsNone(assert_has_item(self.user, self.ITEM_ID))
