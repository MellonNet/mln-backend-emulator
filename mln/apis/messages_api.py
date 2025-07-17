from mln.models.dynamic import Message, User
from mln.services import message as message_services

from mln.apis.utils import *
from mln.apis.json import *

class MessagesApi(View):
  @method_decorator(csrf_exempt)
  @method_decorator(oauth)
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)

  def get(self, request, access_token, id):
    message = get_or_none(Message, id=id)
    if not message:
      return HttpResponse("Message not found", status=404)
    elif message.recipient != access_token.user:
      return HttpResponse(status=403)
    else:
      return JsonResponse(message_response(message))

  def delete(self, request, access_token, id):
    message = get_or_none(Message, id=id)
    if not message:
      return HttpResponse("Message not found", status=404)
    elif message.recipient != access_token.user:
      return HttpResponse(status=403)
    else:
      message.delete()
      return HttpResponse(status=204)
