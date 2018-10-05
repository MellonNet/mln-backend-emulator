from mln.models.dynamic import FriendshipStatus
from mln.tests.models.test_profile import one_user, two_users
from mln.tests.models.test_module import has_harvestable_module, has_harvestable_module_stack
from mln.tests.services.test_friend import friends, pending_friends
from mln.tests.services.test_page import skin_and_color
from mln.tests.setup_testcase import requires, setup, TestCase
from mln.tests.views.api.xml.handler_testcase import req_resp

@setup
@requires(two_users)
def pending_friends_other_way(self):
	self.other_user.profile.outgoing_friendships.create(to_profile=self.user.profile, status=FriendshipStatus.PENDING)

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

class PageSaveLayoutTest(TestCase, metaclass=req_resp):
	SETUP = has_harvestable_module, has_harvestable_module_stack,
	DIR = "page"
	TESTS = "page_save_layout",

class PageSaveOptionsOnlyColumnColorTest(TestCase, metaclass=req_resp):
	SETUP = one_user,
	DIR = "page/page_save_options"
	VOID_TESTS = "only_column_color",

class PageSaveOptionsSkinAndColorTest(TestCase, metaclass=req_resp):
	SETUP = one_user, skin_and_color
	DIR = "page/page_save_options"
	VOID_TESTS = "skin_and_color",
