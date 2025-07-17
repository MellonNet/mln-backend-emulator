from django.http import HttpResponse

from mln.models.dynamic import Message, Attachment, get_or_none
from mln.models.static import MessageBody, ItemInfo

from json_checker import Checker, CheckerError

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

ATTACHMENT_SCHEMA = {
  "item_id": int,
  "qty": int,
}

def attachment_request(json) -> tuple[int, int]:
  try:
    result = Checker(ATTACHMENT_SCHEMA, soft=True).validate(json)
  except CheckerError as error:
    return HttpResponse(error, status=400)

  item_id = result["item_id"]
  qty = result["qty"]

  item = get_or_none(ItemInfo, id=item_id)
  if not item:
    return HttpResponse("Attachment item not found", status=404)

  return (item, qty)
