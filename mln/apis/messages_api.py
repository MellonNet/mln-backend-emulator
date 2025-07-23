from mln.models.dynamic import Message, User
from mln.services import message as message_services

from mln.apis.utils import *
from mln.apis.json import *
from mln.apis.inbox_api import create_message, create_attachment

class MessagesApi(View):
  @method_decorator(csrf_exempt)
  @method_decorator(oauth)
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)

  def get(self, request, access_token, id):
    message = get_message(message_id=id, user=access_token.user)
    if type(message) is HttpResponse: return message
    return JsonResponse(message_response(message))

  def delete(self, request, access_token, id):
    message = get_message(message_id=id, user=access_token.user)
    if type(message) is HttpResponse: return message
    message.delete()
    return HttpResponse(status=204)

def get_message(message_id: int, user: User):
  result = get_or_none(Message, id=message_id)
  if not result:
    return HttpResponse("Message not found", status=404)
  elif result.recipient != user:
    return HttpResponse(status=403)
  else:
    return result

@csrf_exempt
@oauth
@post_json
@check_json(MESSAGE_REQUEST_SCHEMA)
def reply_to_message(data, access_token, id):
  message = get_message(message_id=id, user=access_token.user)
  if type(message) is HttpResponse: return message
  reply = create_message(data, sender=access_token.user, recipient=message.sender, reply_to=message)
  if type(reply) is HttpResponse: return reply
  attachment = create_attachment(data, reply)
  if type(attachment) is HttpResponse: return attachment
  message_services.send_message(reply, attachment)
  result = message_response(reply)
  return JsonResponse(result, safe=False, status=201)

@csrf_exempt
@oauth
@only_allow("POST")
def mark_read(request, access_token, id):
  message = get_message(message_id=id, user=access_token.user)
  if type(message) is HttpResponse: return message
  message.is_read = True
  message.save()
  return HttpResponse(status=204)
