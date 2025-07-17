from django.contrib.auth.models import User

from ....models.dynamic import get_or_none, Friendship, FriendshipStatus
from ....models.static import ItemType
from ....services.page import page_save_layout

def handle_page_get_new(viewing_user, request):
	page_owner_name = request.get("pageOwner")
	is_private_view = page_owner_name is None
	if is_private_view:
		page_owner = viewing_user
	else:
		page_owner = User.objects.get(username=page_owner_name)

	viewing_own = not is_private_view and page_owner == viewing_user

	# needed to display friend list (both private and public)
	friends = []
	if page_owner.profile.is_networker:
		incoming = page_owner.incoming_friendships.filter(from_user__profile__is_networker=True)
		outgoing = page_owner.outgoing_friendships.filter(to_user__profile__is_networker=True)
	else:
		incoming = page_owner.incoming_friendships.all()
		outgoing = page_owner.outgoing_friendships.all()

	for friendlist, is_from in ((outgoing, True), (incoming, False)):
		for friendship in friendlist:
			if not is_private_view:
				if friendship.status != FriendshipStatus.FRIEND:
					continue
			if is_from:
				friend = friendship.to_user
			else:
				friend = friendship.from_user

			if friendship.status == FriendshipStatus.PENDING:
				if is_from:
					status = "Pending Out"
				else:
					status = "Pending In"
			else:
				status = FriendshipStatus(friendship.status).name.title()
			friends.append((friendship, friend, status))

	friendship_status = None
	if viewing_user.is_authenticated:
		viewing_user.profile.update_available_votes()
		if not is_private_view:
			# needed to display friend status on other people's pages
			friendship = get_or_none(Friendship, from_user=viewing_user, to_user=page_owner)
			if friendship is None:
				friendship = get_or_none(Friendship, from_user=page_owner, to_user=viewing_user)

			if friendship:
				friendship_status = FriendshipStatus(friendship.status).name.title()
				if friendship_status == "Pending":
					if friendship.from_user == viewing_user:
						friendship_status = "Pending Out"
					else:
						friendship_status = "Pending In"

	# For public views, exclude friends who are both networkers and marked as secret.
	# Secret networkers can still see their own complete friend list.
	if not is_private_view and not viewing_own:
		friends = [
			(friendship, friend, status)
			for (friendship, friend, status) in friends
			if not (friend.profile.is_networker and friend.profile.is_secret)
		]

	context = {
		"page_owner": page_owner,
		"viewing_user": viewing_user,
		"is_private_view": is_private_view,
		# Code cannot safely check "not is_private_view" because it may be None elsewhere
		# Code can safely check "is_public_view" anywhere because it'll only exist here
		"is_public_view": not is_private_view,
		"calc_yield": viewing_own,
		"friends": friends,
		"friendship_status": friendship_status
	}

	if not is_private_view:
		context["badges"] = page_owner.inventory.filter(item__type=ItemType.BADGE)

	return context

def handle_page_save_layout(user, request):
	modules = []
	for module_elem in request.findall("result/item"):
		instance_id = module_elem.get("instanceID")
		if instance_id == "00000000-0000-0000-0000-000000000000":
			instance_id = None
		else:
			instance_id = int(instance_id)
		item_id = int(module_elem.get("itemID"))
		details = module_elem.find("details")
		pos_x = int(details.get("posx"))
		pos_y = int(details.get("posy"))
		modules.append((instance_id, item_id, pos_x, pos_y))
	page_save_layout(user, modules)
	return {"user": user}

def handle_page_save_options(user, request):
	settings = request.find("result/settings/color")
	if settings.get("skinID") == "undefined":
		skin_id = None
	else:
		skin_id = int(settings.get("skinID"))
	if settings.get("colorID") == "undefined":
		color_id = None
	else:
		color_id = int(settings.get("colorID"))
	column_color_id = int(settings.get("columnColorID"))
	user.profile.page_skin_id = skin_id
	user.profile.page_color_id = color_id
	user.profile.page_column_color_id = column_color_id
	user.profile.save()
