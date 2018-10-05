from mln.tests.handlers.handler_testcase import req_resp
from mln.tests.services.test_message import attachment, easy_reply_body, message
from mln.tests.setup_testcase import requires, setup, TestCase
from mln.tests.services.test_friend import friends
from mln.tests.test_profile import item, one_user

@setup
@requires(item, one_user)
def user_has_item(self):
	self.user.profile.add_inv_item(self.ITEM_ID, 1)

class MessageTest(TestCase, metaclass=req_resp):
	SETUP = message,
	DIR = "message"
	TESTS = "message_get", "message_list"
	VOID_TESTS = "message_delete",

class MessageSendTest(TestCase, metaclass=req_resp):
	SETUP = friends,
	DIR = "message"
	VOID_TESTS = "message_send",

class MessageSendWithAttachmentTest(TestCase, metaclass=req_resp):
	SETUP = friends, user_has_item
	DIR = "message"
	VOID_TESTS = "message_send_with_attachment",

class MessageEasyReplyTest(TestCase, metaclass=req_resp):
	SETUP = easy_reply_body, message, friends
	DIR = "message"
	VOID_TESTS = "message_easy_reply",

class MessageEasyReplyWithAttachmentTest(TestCase, metaclass=req_resp):
	SETUP = easy_reply_body, message, friends, user_has_item
	DIR = "message"
	VOID_TESTS = "message_easy_reply_with_attachments",

class MessageDetachTest(TestCase, metaclass=req_resp):
	SETUP = attachment,
	DIR = "message"
	VOID_TESTS = "message_detach",
