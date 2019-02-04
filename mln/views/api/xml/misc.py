from ....models.dynamic import AboutMe
from ....services.misc import inventory_module_get, use_blueprint

def handle_blueprint_use(user, request):
	blueprint_id = int(request.get("blueprintID"))
	use_blueprint(user, blueprint_id)

def handle_inventory_module_get(user, request):
	return {"module_stacks": inventory_module_get(user)}

def handle_user_get_my_avatar(user, result):
	"""Doesn't actually seem to be necessary since the avatar is already included in the page?"""
	return {"user": user}

def handle_user_save_my_avatar(user, request):
	profile = request.find("result/userProfile")
	user.profile.avatar = profile.get("avatar")
	user.profile.save()

def handle_user_save_my_statements(user, request):
	statements = request.findall("statements/statement")
	if len(statements) != 6:
		raise ValueError("Incorrect number of statements")
	attrs = {}
	for i, statement in enumerate(statements):
		attrs["question_%i_id" % i] = int(statement.get("question"))
		attrs["answer_%i_id" % i] = int(statement.get("answer"))
	about_me, created = AboutMe.objects.get_or_create(user=user, defaults=attrs)
	if not created:
		for key, value in attrs.items():
			setattr(about_me, key, value)
		about_me.save()
