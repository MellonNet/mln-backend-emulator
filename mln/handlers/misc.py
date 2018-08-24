"""Handlers that don't belong in any other group."""
from ..models.static import ItemInfo, ItemType
from .utils import uuid_int

def handle_blueprint_use(user, request):
	blueprint_id = uuid_int(request.get("blueprintID"))
	user.profile.use_blueprint(blueprint_id)

def handle_inventory_module_get(user, request):
	"""
	Return all modules available in the page builder.
	Networkers have access to all MLN modules, while normal users only have access to those in their inventory.
	"""
	module_stacks = []
	if user.profile.is_networker:
		for module in ItemInfo.objects.filter(type=ItemType.MODULE.value):
			module_stacks.append((module.id, 1))
	else:
		for stack in user.inventory.filter(item__type=ItemType.MODULE.value).all():
			module_stacks.append((stack.item_id, stack.qty))
	return {"module_stacks": module_stacks}

def handle_user_get_my_avatar(user, result):
	"""Doesn't actually seem to be necessary since the avatar is already included in the page?"""
	return

def handle_user_save_my_avatar(user, request):
	"""Save the user's avatar when the user updates it."""
	profile = request.find("result/userProfile")
	user.profile.avatar = profile.get("avatar")
	user.profile.save()

def handle_user_save_my_statements(user, request):
	"""Save the "About me" statements when a user updates them."""
	for statement in request.findall("statements/statement"):
		order = statement.get("order")
		setattr(user.profile, "statement_%s_q_id" % order, uuid_int(statement.get("question")))
		setattr(user.profile, "statement_%s_a_id" % order, uuid_int(statement.get("answer")))
	user.profile.save()
