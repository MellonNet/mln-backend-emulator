from ..services.misc import inventory_module_get, use_blueprint, user_save_my_avatar, user_save_my_statements

def handle_blueprint_use(user, request):
	blueprint_id = int(request.get("blueprintID"))
	use_blueprint(user, blueprint_id)

def handle_inventory_module_get(user, request):
	return {"module_stacks": inventory_module_get(user)}

def handle_user_get_my_avatar(user, result):
	"""Doesn't actually seem to be necessary since the avatar is already included in the page?"""
	return

def handle_user_save_my_avatar(user, request):
	profile = request.find("result/userProfile")
	user_save_my_avatar(user, profile.get("avatar"))

def handle_user_save_my_statements(user, request):
	statements = []
	for statement in request.findall("statements/statement"):
		statements.append((int(statement.get("question")), int(statement.get("answer"))))
	user_save_my_statements(user, statements)
