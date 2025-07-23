from mln.models.dynamic import User, Profile

from mln.services.friend import get_friendship, send_friend_invite
from mln.services.webhooks import run_friendship_webhooks
from mln.apis.utils import *
from mln.apis.json import *

@csrf_exempt
@oauth
@only_allow("GET")
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
        run_friendship_webhooks(friendship, user)
      return JsonResponse(friendship_response(friendship), safe=False)
    elif friendship.status == FriendshipStatus.BLOCKED:
      if friendship.to_user == user:
        return HttpResponse("That user has blocked you", status=403)
      else:
        friendship.status = FriendshipStatus.FRIEND
        friendship.save()
        run_friendship_webhooks(friendship, user)
        return JsonResponse(friendship_response(friendship), safe=False)
    elif friendship.status == FriendshipStatus.FRIEND:
      return JsonResponse(friendship_response(friendship), safe=False)

  def delete(self, request, access_token, username):
    user = access_token.user
    other_user = get_or_none(User, username=username)
    if not other_user:
      return HttpResponse("User not found", status=404)
    friendship = get_friendship(user, other_user)
    if not friendship:
      return HttpResponse(status=204)
    elif friendship.to_user == user and friendship.status == FriendshipStatus.BLOCKED:
      return HttpResponse("That user has blocked you", status=403)
    else:
      friendship.status = FriendshipStatus.REMOVED
      run_friendship_webhooks(friendship, user)
      friendship.delete()
      return HttpResponse(status=204)

@csrf_exempt
@oauth
@only_allow("POST")
def block_user(request, access_token, username):
  user = access_token.user
  other_user = get_or_none(User, username=username)
  if not other_user:
    return HttpResponse("User not found", status=404)

  friendship = get_friendship(user, other_user)
  if not friendship:
    return HttpResponse("Friendship not found", status=404)
  elif friendship.status == FriendshipStatus.BLOCKED:
    if friendship.to_user == user:
      return HttpResponse("That user has blocked you", status=500)
    else:
      return HttpResponse(status=204)
  elif friendship.status == FriendshipStatus.PENDING:
    if friendship.to_user == user:
      # User was sent a request -- accept, then block
      friendship.status = FriendshipStatus.BLOCKED
      friendship.save()
      run_friendship_webhooks(friendship, user)
    else:
      # The other user never accepted the request -- rescind
      friendship.delete()
    return HttpResponse(status=204)
  elif friendship.status == FriendshipStatus.FRIEND:
    if friendship.to_user == user:
      # Flip the direction of the relationship
      friendship.to_user = other_user
      friendship.from_user = user
    friendship.status = FriendshipStatus.BLOCKED
    friendship.save()
    run_friendship_webhooks(friendship, user)
    return HttpResponse(status=204)
