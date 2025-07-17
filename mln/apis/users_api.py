from mln.models.dynamic import User, Profile

from mln.services.friend import get_friendship
from mln.apis.utils import *
from mln.apis.json import *

@csrf_exempt
@oauth
def get_user(request, access_token, username):
  otherUser = get_or_none(User, username=username)
  if not otherUser:
    return HttpResponse("User not found", status=404)
  friendship = get_friendship(access_token.user, otherUser)
  return JsonResponse(user_response(otherUser, friendship))
