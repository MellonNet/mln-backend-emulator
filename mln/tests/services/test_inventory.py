from mln.services.inventory import add_inv_item, remove_inv_item
from mln.tests.setup_testcase import TestCase
from mln.tests.models.test_profile import one_user
from mln.tests.models.test_static import item

class Inventory(TestCase):
	SETUP = item, one_user

	def test_add_inv_item_empty(self):
		add_qty = 10
		add_inv_item(self.user, self.ITEM_ID, add_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=add_qty).exists())

	def test_add_inv_item_exists(self):
		add_qty = 10
		add_inv_item(self.user, self.ITEM_ID, add_qty)
		add_inv_item(self.user, self.ITEM_ID, add_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=add_qty*2).exists())

	def test_remove_inv_item_exists(self):
		add_qty = 10
		remove_qty = 5
		add_inv_item(self.user, self.ITEM_ID, add_qty)
		remove_inv_item(self.user, self.ITEM_ID, remove_qty)
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=add_qty-remove_qty).exists())

	def test_remove_inv_item_delete_stack(self):
		add_qty = 10
		remove_qty = 10
		add_inv_item(self.user, self.ITEM_ID, add_qty)
		remove_inv_item(self.user, self.ITEM_ID, remove_qty)
		self.assertFalse(self.user.inventory.filter(item_id=self.ITEM_ID).exists())

	def test_remove_inv_item_no_stack(self):
		remove_qty = 10
		with self.assertRaises(RuntimeError):
			remove_inv_item(self.user, self.ITEM_ID, remove_qty)

	def test_remove_inv_item_not_enough_items(self):
		add_qty = 5
		remove_qty = 10
		add_inv_item(self.user, self.ITEM_ID, add_qty)
		with self.assertRaises(RuntimeError):
			remove_inv_item(self.user, self.ITEM_ID, remove_qty)
