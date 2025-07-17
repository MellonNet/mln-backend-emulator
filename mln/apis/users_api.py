from mln.models.dynamic import User, Profile

from mln.services.friend import get_friendship, send_friend_invite
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

class FriendshipsApi(View):
  @method_decorator(csrf_exempt)
  @method_decorator(oauth)
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)

  def post(self, data, access_token, username):
    user = access_token.user
    otherUser = get_or_none(User, username=username)
    if not otherUser:
      return HttpResponse("User not found", status=404)

    friendship = get_friendship(user, otherUser)
    if not friendship:
      friendship = send_friend_invite(user=user, recipient_name=username)
      if not friendship:
        # Only networkers can reject friend requests, due to items
        return HttpResponse("This networker doesn't want to be your friend, check your inbox", status=402)
      else:
        return JsonResponse(friendship_response(friendship), safe=False)
    elif friendship.status == FriendshipStatus.PENDING:
      if friendship.to_user == user:
        # Accept the pending request
        friendship.status = FriendshipStatus.FRIEND
        friendship.save()
      return JsonResponse(friendship_response(friendship), safe=False)
    elif friendship.status == FriendshipStatus.BLOCKED:
      return HttpResponse(status=403)
    elif friendship.status == FriendshipStatus.FRIEND:
      return JsonResponse(friendship_response(friendship), safe=False)
