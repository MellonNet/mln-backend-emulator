from django.core.management.base import BaseCommand

from mln.models.dynamic import Message, Profile
from mln.services.message import consolidate

class Command(BaseCommand):
  """
  Consolidates all messages for all users

  Loops through all messages in each user's inbox. If there is already a message in the user's inbox
  with the same message body and sender, then consolidate this message with that one. Consolidation
  in this case means adding this message's attachments to the existing message.
  """
  def handle(self, *args, **options):
    for profile in Profile.objects.all():
      user = profile.user
      if profile.is_networker: continue
      unique_messages = {}  # {(MessageBody.id, Sender.id): Message}
      for message in Message.objects.filter(recipient_id=user):
        ids = (message.body.id, message.sender.id)
        already_sent = unique_messages.get(ids)
        if not already_sent:
          unique_messages[ids] = message
        else:
          consolidate(already_sent, message)
          message.delete()
