"""Mail functionality handlers."""
from ..models.dynamic import Message
from .utils import uuid_int

def handle_message_delete(user, request):
	"""Delete a message from the user's inbox."""
	message = handle_message_detach(user, request)
	message.delete()

def handle_message_detach(user, request):
	"""Collect an attachment from a message, place it in the user's inventory."""
	message_id = int(request.get("messageID"))
	message = Message.objects.get(id=message_id)
	for attachment in message.attachments.all():
		user.profile.add_inv_item(attachment.item_id, attachment.qty)
	message.attachments.all().delete()
	return message

def handle_message_easy_reply(user, request):
	"""Send a reply from a list of suggested replies."""
	recipient_id = int(request.get("recipientID"))
	org_body_id = uuid_int(request.get("orgBodyID"))
	body_id = uuid_int(request.get("bodyID"))
	return Message.objects.create(sender=user, recipient_id=recipient_id, body_id=body_id, reply_body_id=org_body_id)

def handle_message_easy_reply_with_attachments(user, request):
	"""Like easy reply, but also attach items."""
	message = handle_message_easy_reply(user, request)
	create_attachment(message, request)

def handle_message_get(user, request):
	"""Open a message to read. Return sender avatar and attachment info. Mark the message as read."""
	message_id = int(request.get("messageID"))
	message = Message.objects.get(id=message_id)
	message.is_read = True
	message.save()
	return {"message": message}

def handle_message_list(user, request):
	"""List all messages in the user's inbox."""
	messages = user.messages.all().order_by("-id")
	return {"messages": messages}

def handle_message_send(user, request):
	"""Send a message to someone."""
	recipient_id = int(request.get("recipientID"))
	body_id = uuid_int(request.get("bodyID"))
	return Message.objects.create(sender=user, recipient_id=recipient_id, body_id=body_id)

def handle_message_send_with_attachment(user, request):
	"""Send a message with attachment."""
	message = handle_message_send(user, request)
	create_attachment(message, request)

def create_attachment(message, request):
	"""Remove items from the user's inventory and attach it to the message."""
	attachment_item_id = uuid_int(request.get("itemID"))
	attachment_qty = int(request.get("qty"))
	message.sender.profile.remove_inv_item(attachment_item_id, attachment_qty)
	message.attachments.create(item_id=attachment_item_id, qty=attachment_qty, message=message)
