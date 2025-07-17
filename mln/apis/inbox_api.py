from mln.models.dynamic import Message
from mln.apis.utils import *
from mln.apis.json import *

@csrf_exempt
@oauth
def get_messages(request, access_token):
  # TODO: Support ?count=n
  query = Message.objects.filter(recipient=access_token.user).all()
  result = [
    message_response(message)
    for message in query
  ]

  return JsonResponse(result, safe=False)
