from mln.models.dynamic import Message, Attachment
from mln.models.static import MessageBody

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
