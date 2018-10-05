from mln.models.static import Answer, BlueprintInfo, BlueprintRequirement, ItemInfo, ItemType, Question
from mln.services.misc import inventory_module_get, use_blueprint, user_save_my_avatar, user_save_my_statements
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.models.test_profile import item, networker, one_user

@cls_setup
def module(cls):
	cls.MODULE_ITEM_ID = ItemInfo.objects.create(name="Module Item", type=ItemType.MODULE).id

@cls_setup
def module_2(cls):
	cls.MODULE_ITEM_2_ID = ItemInfo.objects.create(name="Module Item 2", type=ItemType.MODULE).id

@setup
@requires(module, one_user)
def has_module(self):
	self.user.profile.add_inv_item(self.MODULE_ITEM_ID)

@cls_setup
@requires(item)
def item_blueprint(cls):
	cls.REQUIREMENT_ID = ItemInfo.objects.create(name="Requirement", type=ItemType.ITEM).id
	cls.BLUEPRINT_ID = ItemInfo.objects.create(name="Test Item Blueprint", type=ItemType.BLUEPRINT).id
	BlueprintInfo.objects.create(item_id=cls.BLUEPRINT_ID, build_id=cls.ITEM_ID)
	BlueprintRequirement.objects.create(blueprint_item_id=cls.BLUEPRINT_ID, item_id=cls.REQUIREMENT_ID, qty=1)

@setup
@requires(item_blueprint, one_user)
def has_item_blueprint(self):
	self.user.profile.add_inv_item(self.BLUEPRINT_ID)

@setup
@requires(item_blueprint, one_user)
def has_requirement(self):
	self.user.profile.add_inv_item(self.REQUIREMENT_ID)

@cls_setup
def statements(cls):
	cls.STATEMENTS = {}
	for i in range(10):
		question_id = Question.objects.create(text="Question %i" % i, mandatory=i == 0).id
		answers = []
		for j in range(10):
			answers.append(Answer.objects.create(text="Answer %i %i" % (i, j), question_id=question_id).id)
		cls.STATEMENTS[question_id] = answers

class InventoryModuleGetUserNoModulesTest(TestCase):
	SETUP = module, one_user

	def test_inventory_module_get(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 0)

class InventoryModuleGetUserHasModuleTest(TestCase):
	SETUP = has_module,

	def test_inventory_module_get(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 1)
		self.assertIn((self.MODULE_ITEM_ID, 1), module_stacks)

class InventoryModuleGetNetworkerNoModulesTest(TestCase):
	SETUP = module, module_2, networker

	def test_inventory_module_get(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 2)
		self.assertIn((self.MODULE_ITEM_ID, 1), module_stacks)
		self.assertIn((self.MODULE_ITEM_2_ID, 1), module_stacks)

class InventoryModuleGetNetworkerHasModuleTest(TestCase):
	SETUP = has_module, module_2, networker

	def test_inventory_module_get(self):
		module_stacks = inventory_module_get(self.user)
		self.assertEqual(len(module_stacks), 2)
		self.assertIn((self.MODULE_ITEM_ID, 1), module_stacks)
		self.assertIn((self.MODULE_ITEM_2_ID, 1), module_stacks)

class UseBlueprintNoBlueprintTest(TestCase):
	SETUP = item_blueprint, one_user

	def test_use_blueprint_no_blueprint(self):
		with self.assertRaises(RuntimeError):
			use_blueprint(self.user, self.BLUEPRINT_ID)

class UseBlueprintRequirementsNotMetTest(TestCase):
	SETUP = has_item_blueprint,

	def test_use_blueprint_requirements_not_met(self):
		with self.assertRaises(RuntimeError):
			use_blueprint(self.user, self.BLUEPRINT_ID)

class UseBlueprintOkTest(TestCase):
	SETUP = has_item_blueprint, has_requirement

	def test_use_blueprint_ok(self):
		use_blueprint(self.user, self.BLUEPRINT_ID)
		self.assertFalse(self.user.inventory.filter(item_id=self.REQUIREMENT_ID).exists())
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=1).exists())

class UserSaveMyAvatarTest(TestCase):
	SETUP = one_user,

	def test_user_save_my_avatar_no_parts(self):
		with self.assertRaises(ValueError):
			user_save_my_avatar(self.user, "test")

	def test_user_save_my_avatar_wrong_theme(self):
		with self.assertRaises(ValueError):
			user_save_my_avatar(self.user, "1#3,6,22,20,29,1,3,5,2,3,2,2,1,1")

	def test_user_save_my_avatar_wrong_number_of_data(self):
		with self.assertRaises(ValueError):
			user_save_my_avatar(self.user, "0#3,3,6,22,20,29,1,3,5,2,3,2,2,1,1")

	def test_user_save_my_avatar_ok(self):
		avatar = "0#3,6,22,20,29,1,3,5,2,3,2,2,1,1"
		user_save_my_avatar(self.user, avatar)
		self.assertEqual(self.user.profile.avatar, avatar)

class UserSaveMyAvatarNetworkerTest(TestCase):
	SETUP = networker,

	def test_user_save_my_avatar_2_parts(self):
		with self.assertRaises(ValueError):
			user_save_my_avatar(self.user, "0#3,6,22,20,29,1,3,5,2,3,2,2,1,1")

	def test_user_save_my_avatar_ok(self):
		avatar = "1#3,6,22,20,29,1,3,5,2,3,2,2,1,1"
		user_save_my_avatar(self.user, avatar+"#n")
		self.assertEqual(self.user.profile.avatar, avatar)

class UserSaveMyStatementsTest(TestCase):
	SETUP = statements, one_user

	def test_user_save_my_statements_no_statements(self):
		with self.assertRaises(ValueError):
			user_save_my_statements(self.user, [])

	def test_user_save_my_statements_wrong_answers(self):
		statements = []
		i = 0
		first_question_id = None
		for question_id, answers in self.STATEMENTS.items():
			if first_question_id is None:
				first_question_id = question_id
				continue
			statements.append((first_question_id, answers[0]))
			i += 1
			if i == 6:
				break
		with self.assertRaises(ValueError):
			user_save_my_statements(self.user, statements)

	def test_user_save_my_statements_duplicate_questions(self):
		question_id = next(iter(self.STATEMENTS))
		answer_id = self.STATEMENTS[question_id][0]
		statements = ((question_id, answer_id),) * 6
		with self.assertRaises(ValueError):
			user_save_my_statements(self.user, statements)

	def test_user_save_my_statements_mandatory_not_supplied(self):
		statements = []
		i = 0
		for question_id, answers in self.STATEMENTS.items():
			if question_id == 1:
				continue
			statements.append((question_id, answers[0]))
			i += 1
			if i == 6:
				break
		with self.assertRaises(ValueError):
			user_save_my_statements(self.user, statements)

	def test_user_save_my_statements_ok(self):
		statements = []
		i = 0
		for question_id, answers in self.STATEMENTS.items():
			statements.append((question_id, answers[0]))
			i += 1
			if i == 6:
				break
		user_save_my_statements(self.user, statements)
		for i in range(6):
			self.assertEqual(getattr(self.user.profile, "statement_%i_question_id" % i), statements[i][0])
			self.assertEqual(getattr(self.user.profile, "statement_%i_answer_id" % i), statements[i][1])
