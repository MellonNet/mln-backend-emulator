from mln.tests.models.test_profile import item, one_user, user_has_item
from mln.tests.services.test_message import attachment, body, easy_reply_body, message
from mln.tests.setup_testcase import requires, setup, TestCase
from mln.tests.services.test_friend import friends
from mln.tests.views.api.xml.handler_testcase import req_resp

@setup
@requires(attachment)
def message_extra_data(self):
	self.message.reply_body = self.BODY
	self.message.save()

class MessageTest(TestCase, metaclass=req_resp):
	SETUP = message_extra_data,
	DIR = "message"
	TESTS = "message_get", "message_list"
	VOID_TESTS = "message_delete",

class MessageSendTest(TestCase, metaclass=req_resp):
	SETUP = body, friends
	DIR = "message"
	VOID_TESTS = "message_send",

class MessageSendWithAttachmentTest(TestCase, metaclass=req_resp):
	SETUP = body, friends, user_has_item
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
