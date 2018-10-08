from mln.models.dynamic import FriendshipStatus
from mln.models.static import ItemInfo, ItemType
from mln.tests.models.test_profile import one_user, two_users
from mln.tests.models.test_module import has_harvestable_module, has_harvestable_module_stack
from mln.tests.services.test_friend import friends, pending_friends
from mln.tests.services.test_misc import statements
from mln.tests.services.test_page import has_skin
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.views.api.xml.handler_testcase import req_resp

@cls_setup
def badge(self):
	self.BADGE_ID = ItemInfo.objects.create(name="Badge", type=ItemType.BADGE).id

@setup
@requires(two_users)
def pending_friends_other_way(self):
	self.other_user.profile.outgoing_friendships.create(to_profile=self.user.profile, status=FriendshipStatus.PENDING)

@setup
@requires(badge, statements, has_skin)
def user_extra_data(self):
	self.user.profile.add_inv_item(self.BADGE_ID)
	self.user.profile.page_skin_id = self.SKIN_ID
	self.user.profile.page_color_id = self.COLOR_ID
	self.user.profile.page_column_color_id = 0
	i = 0
	for question_id, answers in self.STATEMENTS.items():
		setattr(self.user.profile, "statement_%s_question_id" % i, question_id)
		setattr(self.user.profile, "statement_%s_answer_id" % i, answers[0])
		i += 1
		if i == 6:
			break
	self.user.profile.save()

class PageGetNewFriendsTest(TestCase, metaclass=req_resp):
	SETUP = friends,
	DIR = "page/page_get_new/friends"
	TESTS = "public_view_own",

class PageGetNewPendingFriendsTest(TestCase, metaclass=req_resp):
	SETUP = pending_friends,
	DIR = "page/page_get_new/pending"
	TESTS = "public_view_other", "private_view"

class PageGetNewPendingOtherWayTest(TestCase, metaclass=req_resp):
	SETUP = pending_friends_other_way,
	DIR = "page/page_get_new/pending_other_way"
	TESTS = "public_view_other", "private_view"

class PageGetNewExtraDataTest(TestCase, metaclass=req_resp):
	SETUP = user_extra_data,
	DIR = "page/page_get_new/extra_data"
	TESTS = "public_view", "private_view"

class PageSaveLayoutTest(TestCase, metaclass=req_resp):
	SETUP = has_harvestable_module, has_harvestable_module_stack,
	DIR = "page"
	TESTS = "page_save_layout",

class PageSaveOptionsOnlyColumnColorTest(TestCase, metaclass=req_resp):
	SETUP = one_user,
	DIR = "page/page_save_options"
	VOID_TESTS = "only_column_color",

class PageSaveOptionsSkinAndColorTest(TestCase, metaclass=req_resp):
	SETUP = one_user, has_skin
	DIR = "page/page_save_options"
	VOID_TESTS = "skin_and_color",
