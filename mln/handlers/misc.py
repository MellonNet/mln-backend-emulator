"""Handlers that don't belong in any other group."""
from ..models.static import ItemType
from .utils import uuid_int

def handle_blueprint_use(user, request):
	blueprint_id = uuid_int(request.get("blueprintID"))
	user.profile.use_blueprint(blueprint_id)

def handle_inventory_module_get(user, request):
	"""
	Return all inventory stacks of modules.
	This call is pretty useless since the entire inventory is known to the client already, not sure why it's there.
	This should be removed when replacing the flash frontend.
	"""
	return {"module_stacks": user.inventory.filter(item__type=ItemType.MODULE.value).all()}

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
		setattr(user.profile, "statement_%s_q" % order, uuid_int(statement.get("question")))
		setattr(user.profile, "statement_%s_a" % order, uuid_int(statement.get("answer")))
	user.profile.save()
