from django.core.exceptions import ValidationError

from mln.services.page import page_save_layout
from mln.tests.setup_testcase import TestCase
from mln.tests.models.test_module import harvestable_module, has_harvestable_module, has_harvestable_module_stack, has_setupable_module, setup_setupable_module
from mln.tests.models.test_profile import one_user

class PageSaveLayout_NoStack(TestCase):
	SETUP = harvestable_module, one_user

	def test(self):
		modules = (None, self.HARVESTABLE_MODULE_ID, 0, 0),
		with self.assertRaises(RuntimeError):
			page_save_layout(self.user, modules)

class PageSaveLayout_ExistingStack(TestCase):
	SETUP = has_harvestable_module_stack,

	def test(self):
		modules = (None, self.HARVESTABLE_MODULE_ID, 0, 0),
		page_save_layout(self.user, modules)
		self.assertTrue(self.user.modules.filter(item_id=self.HARVESTABLE_MODULE_ID, pos_x=0, pos_y=0).exists())
		self.assertFalse(self.user.inventory.filter(item_id=self.HARVESTABLE_MODULE_ID).exists())

class PageSaveLayout_ExistingModule(TestCase):
	SETUP = has_harvestable_module,

	def test_update_x_out_of_bounds(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 3, 0),
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)

	def test_update_y_out_of_bounds(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 0, 4),
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)

	def test_update_ok(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 2, 3),
		page_save_layout(self.user, modules)
		module = self.user.modules.get(id=self.h_module.id)
		self.assertEqual(module.pos_x, 2)
		self.assertEqual(module.pos_y, 3)

	def test_remove_ok(self):
		page_save_layout(self.user, [])
		self.assertTrue(self.user.inventory.filter(item_id=self.HARVESTABLE_MODULE_ID, qty=1).exists())
		self.assertFalse(self.user.modules.exists())

class PageSaveLayout_PosTaken(TestCase):
	SETUP = has_harvestable_module, has_harvestable_module_stack

	def test(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 0, 0), (None, self.HARVESTABLE_MODULE_ID, 0, 0)
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)

class PageSaveLayout_NotSetup(TestCase):
	SETUP = has_setupable_module,

	def test(self):
		page_save_layout(self.user, [])
		self.assertFalse(self.user.inventory.filter(item_id=self.ITEM_ID).exists())

class PageSaveLayout_IsSetup(TestCase):
	SETUP = setup_setupable_module,

	def test(self):
		page_save_layout(self.user, [])
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=10).exists())

class PageSaveLayout_Transaction(TestCase):
	SETUP = has_harvestable_module, has_setupable_module

	def test(self):
		modules = (self.h_module.id, self.HARVESTABLE_MODULE_ID, 0, 3), (self.s_module.id, self.SETUPABLE_MODULE_ID, 5, 5)
		with self.assertRaises(ValidationError):
			page_save_layout(self.user, modules)
		self.assertTrue(self.user.modules.filter(id=self.h_module.id, pos_x=0, pos_y=0).exists())
		self.assertTrue(self.user.modules.filter(id=self.s_module.id, pos_x=0, pos_y=1).exists())
