from django.core.exceptions import ValidationError

from mln.services.page import page_save_layout
from mln.tests.setup_testcase import TestCase
from mln.tests.models.test_module import harvestable_module, has_harvestable_module, has_harvestable_module_stack, has_setupable_module, setup_setupable_module
from mln.tests.models.test_profile import item, one_user, user_has_item

class PageSaveLayoutTest(TestCase):
	SETUP = harvestable_module, one_user

	def test_page_save_layout_create_no_stack(self):
		modules = (None, self.HARVESTABLE_MODULE_ID, 0, 0),
		with self.assertRaises(RuntimeError):
			page_save_layout(self.user, modules)

class PageSaveLayoutExistingStackTest(TestCase):
	SETUP = has_harvestable_module_stack,

	def test_page_save_layout_create_ok(self):
		modules = (None, self.HARVESTABLE_MODULE_ID, 0, 0),
		page_save_layout(self.user, modules)
		self.assertTrue(self.user.modules.filter(item_id=self.HARVESTABLE_MODULE_ID, pos_x=0, pos_y=0).exists())
		self.assertFalse(self.user.inventory.filter(item_id=self.HARVESTABLE_MODULE_ID).exists())

class PageSaveLayoutExistingModuleTest(TestCase):
	SETUP = has_harvestable_module,

	def test_page_save_layout_update_x_out_of_bounds(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 3, 0),
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)

	def test_page_save_layout_update_y_out_of_bounds(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 0, 4),
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)

	def test_page_save_layout_update_ok(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 2, 3),
		page_save_layout(self.user, modules)
		module = self.user.modules.get(id=self.h_module.id)
		self.assertEqual(module.pos_x, 2)
		self.assertEqual(module.pos_y, 3)

	def test_page_save_layout_remove_ok(self):
		page_save_layout(self.user, [])
		self.assertTrue(self.user.inventory.filter(item_id=self.HARVESTABLE_MODULE_ID, qty=1).exists())
		self.assertFalse(self.user.modules.exists())

class PageSaveLayoutPosTakenTest(TestCase):
	SETUP = has_harvestable_module, has_harvestable_module_stack

	def test_page_save_layout_pos_taken(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 0, 0), (None, self.HARVESTABLE_MODULE_ID, 0, 0)
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)

class PageSaveLayoutNotSetupTest(TestCase):
	SETUP = has_setupable_module,

	def test_page_save_layout_setup(self):
		page_save_layout(self.user, [])
		self.assertFalse(self.user.inventory.filter(item_id=self.ITEM_ID).exists())

class PageSaveLayoutIsSetupTest(TestCase):
	SETUP = setup_setupable_module,

	def test_page_save_layout_setup(self):
		page_save_layout(self.user, [])
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=10).exists())

class PageSaveLayoutTransactionTest(TestCase):
	SETUP = has_harvestable_module, has_setupable_module

	def test_page_save_layout_transaction(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 0, 3), (self.s_module.id, self.SETUPABLE_MODULE_ID, 5, 5)
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)
		self.assertTrue(self.user.modules.filter(id=self.h_module.id, pos_x=0, pos_y=0).exists())
		self.assertTrue(self.user.modules.filter(id=self.s_module.id, pos_x=0, pos_y=1).exists())
