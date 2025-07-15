from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from ..models.dynamic import get_or_none
from ..models.static import CoastGuardMessage
from .inventory import has_item
from .message import send_template
from . import oauth_api

COAST_GUARD_CLIENT_ID = "bf74c09a-09a0-4cfe-a00c-40755c6a8ad2"

BADGE_IDS = [
  # The item IDs of the Coast Guard rank message templates, in rank order
  76290,  # Coast Guard Badge, rank 1
  76291,  # Coast Guard Badge, rank 2
  76292,  # Coast Guard Badge, rank 3
  76293,  # Coast Guard Badge, rank 4
  76294,  # Coast Guard Badge, rank 5
]

@csrf_exempt
def submit_rank(request):
  data = oauth_api.parse_json_request(request)
  if type(data) is HttpResponse: return data

  user = oauth_api.authenticate_request(data)
  if type(user) is HttpResponse: return user

  rank = data.get("rank", None)
  if not rank or rank not in [1, 2, 3, 4, 5]:
    return HttpResponse("Invalid or missing rank", status=400)

  badge = BADGE_IDS[rank - 1]
  has_badge = has_item(user, badge)
  if has_badge:
    return HttpResponse("The user already has that badge", status=204)

  message = get_or_none(CoastGuardMessage, rank=rank)
  if not message:
    return HttpResponse("Could not find message template", status=500)

  send_template(message.template, message.networker, user)

  return HttpResponse(status=200)
