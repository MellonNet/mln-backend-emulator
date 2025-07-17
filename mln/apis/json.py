from django.http import HttpResponse

from mln.models.dynamic import Message, Attachment, get_or_none
from mln.models.static import MessageBody, ItemInfo

def attachment_response(attachment: Attachment): return {
  "id": attachment.item.id,
  "name": attachment.item.name,
  "qty": attachment.qty,
}

def message_body_response(body: MessageBody): return {
  "body_id": body.id,
  "subject": body.subject,
  "body": body.text,
}

def message_response(message: Message): return {
  "id": message.id,
  "sender_id": message.sender.id,
  "sender_username": message.sender.username,
  **message_body_response(message.body),
  "attachments": [
    attachment_response(attachment)
    for attachment in message.attachments.all()
  ],
  "replies": [
    message_body_response(reply)
    for reply in message.body.easy_replies.all()
  ],
}

def attachment_request(json) -> tuple[ItemInfo, int]:
  item_id = json.get("item_id")
  print(f"Item: {item_id}")
  if not item_id or type(item_id) is not int:
    return HttpResponse("Invalid or missing attachment.item_id", status=400)

  item = get_or_none(ItemInfo, id=item_id)
  if not item:
    return HttpResponse("Attachment item not found", status=404)

  qty = json.get("qty")
  if not qty or type(qty) is not int:
    return HttpResponse("Invalid or missing attachment.qty", status=400)

  return (item, qty)
