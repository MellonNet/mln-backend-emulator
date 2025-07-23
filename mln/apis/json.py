from django.http import HttpResponse
from functools import wraps
from json_checker import Checker, CheckerError, OptionalKey

from mln.models.dynamic import Message, Attachment, get_or_none, Friendship, FriendshipStatus, User, InventoryStack
from mln.services.inventory import get_badges
from mln.models.static import MessageBody, ItemInfo

def attachment_response(attachment: Attachment): return {
  "item_id": attachment.item.id,
  "name": attachment.item.name,
  "qty": attachment.qty,
}

def message_body_response(body: MessageBody): return {
  "id": body.id,
  "subject": body.subject,
  "text": body.text,
}

def message_response(message: Message): return {
  "id": message.id,
  "sender_id": message.sender.id,
  "sender_username": message.sender.username,
  "body": message_body_response(message.body),
  "is_read": message.is_read,
  "attachments": [
    attachment_response(attachment)
    for attachment in message.attachments.all()
  ],
  "replies": [
    message_body_response(reply)
    for reply in message.body.easy_replies.all()
  ],
}

def badge_response(badge: InventoryStack): return {
  "id": badge.item.id,
  "name": badge.item.name,
  # TODO: description and thumbnail
}

def friendship_response(friendship: Friendship):
  if friendship is None:
    return "none"
  else:
    return friendship.status.name.lower()

def full_friendship_response(friendship: Friendship): return {
  "from_user_id": friendship.from_user.id,
  "from_username": friendship.from_user.username,
  "to_user_id": friendship.to_user.id,
  "to_username": friendship.to_user.username,
  "status": friendship_response(friendship)
}

def user_response(user: User, friendship: Friendship): return {
  "username": user.username,
  "page_url": f"/mln/public_view/{user.username}",
  "rank": user.profile.rank,
  "is_networker": user.profile.is_networker,
  "friendship_status": friendship_response(friendship),
  "badges": [
    badge_response(badge)
    for badge in get_badges(user)
  ]
}

ATTACHMENT_SCHEMA = {
  "item_id": int,
  "qty": int,
}

MESSAGE_REQUEST_SCHEMA = {
  "body_id": int,
  OptionalKey("attachment"): ATTACHMENT_SCHEMA,
}

SEND_MESSAGE_SCHEMA = {
  "recipient": str,
  **MESSAGE_REQUEST_SCHEMA,
}

def attachment_request(json) -> tuple[int, int]:
  item_id = json["item_id"]
  item = get_or_none(ItemInfo, id=item_id)
  if not item:
    return HttpResponse("Attachment item not found", status=404)

  qty = json["qty"]
  if qty <= 0:
    return HttpResponse("Cannot attach 0 or less of something", status=400)
  return (item, qty)

def check_json(schema):
  def decorator(func):
    @wraps(func)
    def wrapper(data, *args, **kwargs):
      try:
        checker = Checker(schema, soft=True, ignore_extra_keys=True)
        checker.validate(data)
        return func(data, *args, **kwargs)
      except CheckerError as error:
        return HttpResponse(error, status=400)
    return wrapper
  return decorator
