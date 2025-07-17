import requests

from mln.models.dynamic import Webhook, WebhookType
from mln.apis.json import message_response

def run_message_webhooks(message):
  recipient = message.recipient
  webhooks = Webhook.objects.filter(user=recipient, type=WebhookType.MESSAGES)
  for webhook in webhooks.all():
    body = message_response(message),
    run_webhook(webhook, body)

def run_webhook(webhook, body):
  headers = {
    "Authorization": f"Bearer {webhook.access_token.access_token}",
    "Api-Token": webhook.secret,
  }
  try:
    requests.post(webhook.url, json=body, headers=headers, timeout=0.1)
  except requests.ConnectionError:
    # We don't care if these requests go through
    pass
