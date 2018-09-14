"""Mail functionality handlers."""
from ..services.message import create_attachment, delete_message, detach_attachments, easy_reply, open_message, send_message

def handle_message_delete(user, request):
	message_id = int(request.get("messageID"))
	delete_message(user, message_id)

def handle_message_detach(user, request):
	message_id = int(request.get("messageID"))
	detach_attachments(user, message_id)

def handle_message_easy_reply(user, request):
	recipient_id = int(request.get("recipientID"))
	org_body_id = int(request.get("orgBodyID"))
	body_id = int(request.get("bodyID"))
	return easy_reply(user, recipient_id, org_body_id, body_id)

def handle_message_easy_reply_with_attachments(user, request):
	"""Like easy reply, but also attach items."""
	message = handle_message_easy_reply(user, request)
	handle_create_attachment(request, message)

def handle_message_get(user, request):
	message_id = int(request.get("messageID"))
	message = open_message(user, message_id)
	return {"message": message}

def handle_message_list(user, request):
	"""List all messages in the user's inbox."""
	messages = user.messages.all().order_by("-id")
	return {"messages": messages}

def handle_message_send(user, request):
	recipient_id = int(request.get("recipientID"))
	body_id = int(request.get("bodyID"))
	return send_message(user, recipient_id, body_id)

def handle_message_send_with_attachment(user, request):
	"""Send a message with attachment."""
	message = handle_message_send(user, request)
	handle_create_attachment(request, message)

def handle_create_attachment(request, message):
	item_id = int(request.get("itemID"))
	qty = int(request.get("qty"))
	create_attachment(message, item_id, qty)
