import random
from django.db.models import Q

from mln.models.dynamic import User, Profile, FriendshipStatus
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
@maybe_auth
@only_allow("GET")
def get_user(request, user, username):
  otherUser = get_or_none(User, username__iexact=username)
  if not otherUser:
    return HttpResponse("User not found", status=404)
  if user:
    friendship = get_friendship(user, otherUser)
    response = user_response(otherUser, friendship)
  else:
    response = user_response(otherUser, friendship=None, anonymous=True)
  return JsonResponse(response)

@csrf_exempt
@auth
@only_allow("GET")
def get_random_user(request, user):
  rank_str: str = request.GET.get("rank")
  if not rank_str: return HttpResponse("Must specify a rank", status=400)
  if not rank_str.isnumeric(): return HttpResponse("Rank must be a number", status=400)
  rank = int(rank_str)
  if rank < 0 or rank > 10: return HttpResponse("Rank must be between 0 and 10", status=400)
  profiles = Profile.objects.filter(Q(rank=rank) & Q(is_networker=False))
  if not profiles: return JsonResponse(None, safe=False)
  profile = random.choice(profiles)
  other_user = profile.user
  friendship = get_friendship(user, other_user)
  return JsonResponse(user_response(profile.user, friendship))

class FriendshipsApi(View):
  @method_decorator(csrf_exempt)
  @method_decorator(auth)
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)

  def post(self, data, user, username):
    otherUser = get_or_none(User, username__iexact=username)
    if not otherUser:
      return HttpResponse("User not found", status=404)

    friendship = get_friendship(user, otherUser)
    if not friendship:
      friendship = send_friend_invite(user=user, recipient_name=username)
      if not friendship:
        # Only networkers can reject friend requests, due to items
        return HttpResponse("This networker doesn't want to be your friend, check your inbox", status=402)
      else:
        response = full_friendship_response(friendship, action=f"Sent {username} a friend request")
        return JsonResponse(response, safe=False)
    elif friendship.status == FriendshipStatus.PENDING:
      if friendship.to_user == user:
        # Accept the pending request
        friendship.status = FriendshipStatus.FRIEND
        friendship.save()
        run_friendship_webhooks(friendship, user)
      response = full_friendship_response(friendship, action=f"Accepted {username}'s friend request")
      return JsonResponse(response, safe=False)
    elif friendship.status == FriendshipStatus.BLOCKED:
      if friendship.to_user == user:
        return HttpResponse("That user has blocked you", status=403)
      else:
        friendship.status = FriendshipStatus.FRIEND
        friendship.save()
        run_friendship_webhooks(friendship, user)
        response = full_friendship_response(friendship, action=f"Unblocked {username}")
        return JsonResponse(response, safe=False)
    elif friendship.status == FriendshipStatus.FRIEND:
      response = full_friendship_response(friendship, action=f"{username} was already your friend")
      return JsonResponse(response, safe=False)

  def delete(self, request, user, username):
    other_user = get_or_none(User, username__iexact=username)
    if not other_user:
      return HttpResponse("User not found", status=404)
    friendship = get_friendship(user, other_user)
    if not friendship:
      return HttpResponse(status=204)
    elif friendship.to_user == user and friendship.status == FriendshipStatus.BLOCKED:
      return HttpResponse("That user has blocked you", status=403)
    else:
      friendship.status = None
      run_friendship_webhooks(friendship, user)
      friendship.delete()
      return HttpResponse(status=204)

class UserBlockApi(View):
  @method_decorator(csrf_exempt)
  @method_decorator(auth)
  def dispatch(self, request, *args, **kwargs):
    return super().dispatch(request, *args, **kwargs)

  def delete(self, request, user, username):
    # Do not run webhooks here
    other_user = get_or_none(User, username__iexact=username)
    if not other_user:
      return HttpResponse("User not found", status=404)

    friendship = get_friendship(user, other_user)
    if not friendship:
      return HttpResponse("You were not friends with that user", status=400)

    if friendship.status != FriendshipStatus.BLOCKED:
      return HttpResponse(status=204)

    if friendship.to_user == user:
      return HttpResponse("That user has blocked you", status=400)
    else:
      friendship.status = FriendshipStatus.FRIEND
      friendship.save()  # aww....
      return HttpResponse(status=200)

  def post(self, request, user, username):
    # Do not run webhooks here
    other_user = get_or_none(User, username__iexact=username)
    if not other_user:
      return HttpResponse("User not found", status=404)

    friendship = get_friendship(user, other_user)
    if not friendship:
      return HttpResponse("Friendship not found", status=404)
    elif friendship.status == FriendshipStatus.BLOCKED:
      if friendship.to_user == user:
        return HttpResponse("That user has blocked you", status=400)
      else:
        return HttpResponse(status=204)
    elif friendship.status == FriendshipStatus.PENDING:
      if friendship.to_user == user:
        # User was sent a request -- accept, then block
        friendship.status = FriendshipStatus.BLOCKED
        friendship.save()
      else:
        # The other user never accepted the request -- rescind
        friendship.delete()
      return HttpResponse(status=200)
    elif friendship.status == FriendshipStatus.FRIEND:
      if friendship.to_user == user:
        # Flip the direction of the relationship
        friendship.to_user = other_user
        friendship.from_user = user
      friendship.status = FriendshipStatus.BLOCKED
      friendship.save()
      return HttpResponse(status=200)
