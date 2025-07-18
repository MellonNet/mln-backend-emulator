import requests

from mln.models.dynamic import Webhook, WebhookType
from mln.apis.json import message_response, full_friendship_response

def run_message_webhooks(message):
  recipient = message.recipient
  webhooks = Webhook.objects.filter(user=recipient, type=WebhookType.MESSAGES)
  for webhook in webhooks.all():
    body = message_response(message)
    run_webhook(webhook, body)

def run_friendship_webhooks(friendship, actor):
  if friendship.to_user == actor:
    recipient = friendship.from_user
  else:
    recipient = friendship.to_user
  webhooks = Webhook.objects.filter(user=recipient, type=WebhookType.FRIENDSHIPS)
  for webhook in webhooks.all():
    body = full_friendship_response(friendship)
    run_webhook(webhook, body)

def run_webhook(webhook, body):
  headers = {
    "Authorization": f"Bearer {webhook.access_token.access_token}",
    "Api-Token": webhook.secret,
  }
  # We don't care if these requests go through
  try: requests.post(webhook.url, json=body, headers=headers, timeout=1)
  except requests.ConnectionError: pass
  except requests.exceptions.Timeout: pass
