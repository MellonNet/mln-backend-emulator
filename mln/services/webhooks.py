import requests

from mln.models.dynamic import Webhook, WebhookType, User
from mln.apis.json import message_response, full_friendship_response

def run_message_webhooks(message):
  recipient = message.recipient
  run_webhooks(
    webhooks = Webhook.objects.filter(user=recipient, type=WebhookType.MESSAGES),
    body = message_response(message),
  )

def run_friendship_webhooks(friendship, actor):
  if friendship.to_user == actor:
    recipient = friendship.from_user
  else:
    recipient = friendship.to_user
  run_webhooks(
    webhooks = Webhook.objects.filter(user=recipient, type=WebhookType.FRIENDSHIPS),
    body = full_friendship_response(friendship),
  )

def run_rank_webhooks(user: User): run_webhooks(
  webhooks = Webhook.objects.filter(type=WebhookType.RANK_UP),
  body = {
    "rank": user.profile.rank,
    "username": user.username,
  },
)

def run_badge_webhooks(user: User, badge: str): run_webhooks(
  webhooks = Webhook.objects.filter(type=WebhookType.BADGE),
  body = {
    "badge": badge,
    "username": user.username,
  },
)

def run_webhooks(webhooks, body):
  for webhook in webhooks.all():
    headers = {"Api-Token": webhook.secret}
    if webhook.access_token:  # Not all webhooks have an access token
      headers["Authorization"] = f"Bearer {webhook.access_token.access_token}"

    # We don't care if these requests go through
    try: requests.post(webhook.url, json=body, headers=headers, timeout=1)
    except requests.ConnectionError: pass
    except requests.exceptions.Timeout: pass
