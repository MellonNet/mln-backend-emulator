from mln.tests.models.test_profile import two_users
from mln.tests.services.test_friend import blocked_friends, friends, pending_friends_other_way
from mln.tests.setup_testcase import requires, setup, TestCase
from mln.tests.views.api.xml.handler_testcase import req_resp

class FriendSendInvitationTest(TestCase, metaclass=req_resp):
	SETUP = two_users,
	DIR = "friend"
	VOID_TESTS = "friend_send_invitation",

class FriendProcessInvitationTest(TestCase, metaclass=req_resp):
	SETUP = pending_friends_other_way,
	DIR = "friend"
	VOID_TESTS = "friend_process_invitation",

class FriendTest(TestCase, metaclass=req_resp):
	SETUP = friends,
	DIR = "friend"
	VOID_TESTS = "friend_remove_member", "friend_process_blocking_block"

class FriendProcessBlockingUnblockTest(TestCase, metaclass=req_resp):
	SETUP = blocked_friends,
	DIR = "friend"
	VOID_TESTS = "friend_process_blocking_unblock",
