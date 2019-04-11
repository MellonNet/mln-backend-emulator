from mln.models.static import ItemInfo, ItemType
from mln.models.dynamic import AboutMe
from mln.tests.models.test_profile import color, has_skin, one_user, networker, statements
from mln.tests.models.test_module import has_harvestable_module, has_harvestable_module_stack
from mln.tests.services.test_friend import friends, pending_friends, pending_friends_other_way, two_friends
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.views.api.xml.handler_testcase import req_resp

@cls_setup
def badge(self):
	self.BADGE_ID = ItemInfo.objects.create(name="Badge", type=ItemType.BADGE).id

@setup
@requires(networker, two_friends)
def networker_friends(self):
	self.other_user.profile.is_networker = True
	self.other_user.profile.save()

@setup
@requires(badge, color, statements, has_skin)
def user_extra_data(self):
	self.user.profile.add_inv_item(self.BADGE_ID)
	self.user.profile.page_skin_id = self.SKIN_ID
	self.user.profile.page_color_id = self.COLOR_ID
	self.user.profile.page_column_color_id = 0
	self.user.profile.save()
	about_me = AboutMe(user=self.user)
	i = 0
	for question_id, answers in self.STATEMENTS.items():
		setattr(about_me, "question_%s_id" % i, question_id)
		setattr(about_me, "answer_%s_id" % i, answers[0])
		i += 1
		if i == 6:
			break
	about_me.save()

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

class PageGetNewNetworkerFriendsTest(TestCase, metaclass=req_resp):
	SETUP = networker_friends,
	DIR = "page/page_get_new/networker_friends"
	TESTS = "public_view",

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
	SETUP = color, has_skin
	DIR = "page/page_save_options"
	VOID_TESTS = "skin_and_color",
