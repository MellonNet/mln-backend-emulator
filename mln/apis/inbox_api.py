from mln.models.dynamic import Message, User
from mln.services import message as message_services

from mln.apis.utils import *
from mln.apis.json import *

from json_checker import Checker, CheckerError, OptionalKey

class InboxApi(View):
  @method_decorator(csrf_exempt)
  @method_decorator(oauth)
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)

  def get(self, request, access_token):
    # TODO: Support ?count=n
    query = Message.objects.filter(recipient=access_token.user).all()
    result = [
      message_response(message)
      for message in query
    ]
    return JsonResponse(result, safe=False)

  @method_decorator(post_json)
  @method_decorator(check_json(SEND_MESSAGE_SCHEMA))
  def post(self, data, access_token):
    recipient_username = data.get("recipient")
    recipient = get_or_none(User, username=recipient_username)
    if not recipient:
      return HttpResponse("Recipient not found", status=404)

    body_id = data.get("body_id")
    body = get_or_none(MessageBody, id=body_id)
    if not body:
      return HttpResponse("Message not found", status=404)

    try:
      message = message_services.create_message(
        user=access_token.user,
        recipient_id=recipient.id,
        body_id=body.id,
      )
    except RuntimeError:
      return HttpResponse("You cannot send messages to this user", status=403)

    attachment = None
    attachment_raw = data.get("attachment")
    if attachment_raw:
      attachment = attachment_request(attachment_raw)
      if type(attachment) is HttpResponse: return attachment
      try:
        (item, qty) = attachment
        attachment = message_services.create_attachment(message, item.id, qty)
      except RuntimeError:
        return HttpResponse(f"You do not have {qty} {item.name}(s)", status=402)

    # TODO: Check if items are actually mailable
    message_services.send_message(message, attachment)

    result = message_response(message)
    return JsonResponse(result, safe=False, status=201)
