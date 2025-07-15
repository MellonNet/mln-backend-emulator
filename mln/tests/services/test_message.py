from mln.models import *
from mln.services.inventory import add_inv_item
from mln.services.message import create_attachment, create_message, delete_message, detach_attachments, easy_reply, open_message, send_message
from mln.tests.models.test_dynamic import attachment, body, message
from mln.tests.models.test_profile import networker, other_user_has_item, two_users
from mln.tests.models.test_static import body_category, item
from mln.tests.services.test_friend import friends
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase

@cls_setup
@requires(body)
def other_body(cls):
	cls.REPLY_BODY = MessageBody.objects.create(category_id=cls.BODY_CAT_ID, subject="Reply Body", text="Test Body")

@cls_setup
@requires(other_body)
def easy_reply_body(cls):
	cls.BODY.easy_replies.add(cls.REPLY_BODY)

@setup
@requires(body_category)
def networker_message(self):
	"""Sets up tests for NetworkerReply."""
	self.wrong_message_body_id = MessageBody.objects.create(category_id=self.BODY_CAT_ID, subject="Wrong Message", text="Wrong body").id
	self.correct_message_body_id = MessageBody.objects.create(category_id=self.BODY_CAT_ID, subject="Correct Message", text="Correct body").id
	self.reply_id = MessageBody.objects.create(category_id=self.BODY_CAT_ID, subject="Networker reply", text="This is a response").id
	self.wrong_attachment_id = ItemInfo.objects.create(name="Wrong item", type=ItemType.ITEM).id
	self.correct_attachment_id = ItemInfo.objects.create(name="Correct item", type=ItemType.ITEM).id
	# Create networker's reply
	MessageBody.objects.create(id=MLNMessage.I_DONT_GET_IT, category_id=self.BODY_CAT_ID, subject="I don't get it", text="Invalid message").id
	template = MessageTemplate.objects.create(body_id=self.reply_id)
	NetworkerReply.objects.create(template=template, networker=self.user, trigger_body_id=self.correct_message_body_id)
	NetworkerReply.objects.create(template=template, networker=self.user, trigger_attachment_id=self.correct_attachment_id)
	# Manually add items instead of requiring other_user_has_item to add 2 different items
	add_inv_item(self.other_user, self.wrong_attachment_id, 1)
	add_inv_item(self.other_user, self.correct_attachment_id, 1)

class NoMessage(TestCase):
	SETUP = body, two_users

	def test_send_message_no_friend(self):
		with self.assertRaises(RuntimeError):
			send_message(create_message(self.user, self.other_user.id, self.BODY.id), None)

class NoMessage_Friend(TestCase):
	SETUP = body, friends

	def test_send_message_ok(self):
		message = create_message(self.user, self.other_user.id, self.BODY.id)
		send_message(message, None)
		self.assertTrue(self.other_user.messages.filter(id=message.id, sender_id=self.user.id, body_id=self.BODY.id).exists())
		self.assertFalse(self.user.messages.filter(sender_id=self.other_user).exists())  # ensure no networker reply was sent

class Message(TestCase):
	# other_user is human, user is a networker
	SETUP = message, friends, networker, networker_message

	def test_delete_message_wrong_user(self):
		with self.assertRaises(RuntimeError):
			detach_attachments(self.other_user, self.message.id)

	def test_detach_attachments_wrong_user(self):
		with self.assertRaises(RuntimeError):
			detach_attachments(self.other_user, self.message.id)

	def test_open_message_already_read(self):
		self.message.is_read = True
		self.message.save()
		open_message(self.user, self.message.id)
		self.assertTrue(self.user.messages.get(id=self.message.id).is_read)

	def test_open_message_ok(self):
		open_message(self.user, self.message.id)
		self.assertTrue(self.user.messages.get(id=self.message.id).is_read)

	def test_send_message_wrong_body(self):
		message = create_message(self.other_user, self.user.id, self.wrong_message_body_id)
		send_message(message, None)
		self.assertTrue(self.other_user.messages.filter(sender=self.user, body_id=MLNMessage.I_DONT_GET_IT).exists())

	def test_send_message_wrong_attachment(self):
		# 1. Verify the networker replies with "I don't get it".
		message = create_message(self.other_user, self.user.id, self.wrong_message_body_id)
		attachment = create_attachment(message, self.wrong_attachment_id, 1)
		send_message(message, attachment)
		self.assertTrue(self.other_user.messages.filter(sender=self.user, body_id=MLNMessage.I_DONT_GET_IT).exists())
		# 2. Verify that attachments were sent back
		reply = self.other_user.messages.get(sender=self.user, body_id=MLNMessage.I_DONT_GET_IT)
		self.assertTrue(reply.attachments.filter(item=attachment.item, qty=attachment.qty))

	def test_send_message_correct_body(self):
		# Verify the networker replies with the correct response
		message = create_message(self.other_user, self.user.id, self.correct_message_body_id)
		send_message(message, None)
		self.assertTrue(self.other_user.messages.filter(sender_id=self.user.id, body_id=self.reply_id).exists())

	def test_send_message_correct_attachment(self):
		# Verify the networker replies with the correct response
		message = create_message(self.other_user, self.user.id, self.wrong_message_body_id)
		attachment = create_attachment(message, self.correct_attachment_id, 1)
		send_message(message, attachment)
		self.assertTrue(self.other_user.messages.filter(sender_id=self.user.id, body_id=self.reply_id).exists())

class CreateAttachment_NoStack(TestCase):
	SETUP = message, item

	def test(self):
		with self.assertRaises(RuntimeError):
			create_attachment(self.message, self.ITEM_ID, 1)

class CreateAttachment_ExistingStack(TestCase):
	SETUP = other_user_has_item, message

	def test(self):
		attachment = create_attachment(self.message, self.ITEM_ID, 1)
		send_message(self.message, attachment)
		self.assertFalse(self.other_user.inventory.filter(id=self.ITEM_ID).exists())
		self.assertTrue(self.message.attachments.filter(item_id=self.ITEM_ID, qty=1).exists())

class ExistingAttachment(TestCase):
	SETUP = attachment,

	def check_detach_attachments(self):
		self.assertFalse(self.message.attachments.all().exists())
		self.assertTrue(self.user.inventory.filter(item_id=self.ITEM_ID, qty=1).exists())

	def test_delete_message_ok(self):
		delete_message(self.user, self.message.id)
		self.check_detach_attachments()
		self.assertFalse(self.user.messages.filter(id=self.message.id).exists())

	def test_detach_attachments_ok(self):
		detach_attachments(self.user, self.message.id)
		self.check_detach_attachments()

class EasyReply_NoFriend(TestCase):
	SETUP = easy_reply_body, message

	def test(self):
		with self.assertRaises(RuntimeError):
			easy_reply(self.user, self.other_user.id, self.BODY.id, self.REPLY_BODY.id)

class EasyReply_NoMessage(TestCase):
	SETUP = easy_reply_body, friends

	def test(self):
		with self.assertRaises(RuntimeError):
			easy_reply(self.user, self.other_user.id, self.BODY.id, self.REPLY_BODY.id)

class EasyReply_NotAnEasyReply(TestCase):
	SETUP = other_body, message, friends

	def test(self):
		with self.assertRaises(RuntimeError):
			easy_reply(self.user, self.other_user.id, self.BODY.id, self.REPLY_BODY.id)

class EasyReply_Friend(TestCase):
	SETUP = easy_reply_body, message, friends

	def test(self):
		easy_reply(self.user, self.other_user.id, self.BODY.id, self.REPLY_BODY.id)
		self.assertTrue(self.other_user.messages.filter(sender=self.user, body=self.REPLY_BODY).exists())
