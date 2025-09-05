from mln.models.dynamic import User, Profile, MessageTemplate

from mln.services import message as message_services
from mln.services.friend import get_friendship, send_friend_invite
from mln.services.webhooks import run_friendship_webhooks
from mln.apis.utils import *
from mln.apis.json import *

@csrf_exempt
@auth
@only_allow("GET")
def get_self(request, user):
  return JsonResponse(user_response(user, None))

@csrf_exempt
@auth
@only_allow("GET")
def get_user(request, user, username):
  otherUser = get_or_none(User, username=username)
  if not otherUser:
    return HttpResponse("User not found", status=404)
  friendship = get_friendship(user, otherUser)
  return JsonResponse(user_response(otherUser, friendship))

class FriendshipsApi(View):
  @method_decorator(csrf_exempt)
  @method_decorator(auth)
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)

  def post(self, data, user, username):
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

  def delete(self, request, user, username):
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
@auth
@only_allow("POST")
def block_user(request, user, username):
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

@csrf_exempt
def test(request):
  template = get_or_none(MessageTemplate, id=402)
  return HttpResponse(f"Going to send {template}")
  echo = get_or_none(User, username="Echo")
  if template is None or echo is None:
    return HttpResponse(f"Could not find template or Echo\n- tempplate={template}\n- Echo={echo}", status=500)
  count = 0
  for user in User.objects.all():
    message_services.send_template(template, echo, user)
    count += 1
  return HttpResponse(f"Sent Desctructoid to {count} users")
