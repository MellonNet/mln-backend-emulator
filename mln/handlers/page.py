import uuid

from django.contrib.auth.models import User

from ..models.dynamic import get_or_none, Friendship, FriendshipStatus
from ..models.module import Module
from ..models.static import ItemType
from .utils import uuid_int

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
	for friendlist, is_from in ((page_owner.profile.outgoing_friendships.all(), True), (page_owner.profile.incoming_friendships.all(), False)):
		for friendship in friendlist:
			if not is_private_view:
				if friendship.status != FriendshipStatus.FRIEND.value:
					continue
			if is_from:
				friend = friendship.to_profile.user
			else:
				friend = friendship.from_profile.user

			if friendship.status == FriendshipStatus.PENDING.value:
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
			friendship = get_or_none(Friendship, from_profile=viewing_user.profile, to_profile=page_owner.profile)
			if friendship is None:
				friendship = get_or_none(Friendship, from_profile=page_owner.profile, to_profile=viewing_user.profile)

			if friendship:
				friendship_status = FriendshipStatus(friendship.status).name.title()
				if friendship_status == "Pending":
					if friendship.from_profile == viewing_user.profile:
						friendship_status = "Pending Out"
					else:
						friendship_status = "Pending In"

	context = {
		"page_owner": page_owner,
		"viewing_user": viewing_user,
		"is_private_view": is_private_view,
		"calc_yield": viewing_own,
		"friends": friends,
		"friendship_status": friendship_status
	}

	if not is_private_view:
		context["badges"] = page_owner.inventory.filter(item__type=ItemType.BADGE.value)

	return context

def get_or_create_module(user, elem):
	instance_id = elem.get("instanceID")
	if instance_id == "00000000-0000-0000-0000-000000000000":
		item_id = uuid_int(elem.get("itemID"))
		if not user.profile.is_networker:
			user.profile.remove_inv_item(item_id)
		module = Module.objects.create(item_id=item_id, pos_x=0, pos_y=0, owner=user)
	else:
		module = Module.objects.get(id=int(instance_id))
	return module

def handle_page_save_layout(user, request):
	present_ids = []
	for module_elem in request.findall("result/item"):
		details = module_elem.find("details")
		pos_x = int(details.get("posx"))
		pos_y = int(details.get("posy"))

		module = get_or_create_module(user, module_elem)
		module.pos_x = pos_x
		module.pos_y = pos_y
		module.save()
		present_ids.append(module.id)

	# if a module is not in the supplied list of modules it was removed and should be deleted
	removed_modules = Module.objects.filter(owner=user).exclude(id__in=present_ids)
	if not user.profile.is_networker:
		for module in removed_modules.all():
			user.profile.add_inv_item(module.item_id)
	removed_modules.delete()

	return {}

def handle_page_save_options(user, request):
	settings = request.find("result/settings/color")
	if settings.get("skinID") == "undefined":
		user.profile.page_skin = None
	else:
		user.profile.page_skin_id = uuid_int(settings.get("skinID"))

	color_id = uuid.UUID(settings.get("colorID")).node & 0xff # these UUIDs aren't actually proper UUIDs
	user.profile.page_color_id = color_id
	user.profile.page_column_color_id = int(settings.get("columnColorID"))
	user.profile.save()
