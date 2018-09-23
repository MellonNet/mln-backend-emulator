from ..models.static import Answer, BlueprintInfo, BlueprintRequirement, ItemInfo, ItemType, Question

def inventory_module_get(user):
	"""
	Return all modules available in the page builder.
	Networkers have access to all MLN modules, while normal users only have access to those in their inventory.
	"""
	module_stacks = []
	if user.profile.is_networker:
		for module in ItemInfo.objects.filter(type=ItemType.MODULE):
			module_stacks.append((module.id, 1))
	else:
		for stack in user.inventory.filter(item__type=ItemType.MODULE).all():
			module_stacks.append((stack.item_id, stack.qty))
	return module_stacks

def use_blueprint(user, blueprint_id):
	"""
	Use a blueprint to create a new item and add it to the user's inventory.
	Remove the blueprint's requirements from the user's inventory.
	Raise RuntimeError if the blueprint or a required item is not in the user's inventory.
	"""
	if not user.inventory.filter(item_id=blueprint_id).exists():
		raise RuntimeError("Blueprint not in inventory")
	blueprint_info = BlueprintInfo.objects.get(item_id=blueprint_id)
	requirements = BlueprintRequirement.objects.filter(blueprint_item_id=blueprint_id)
	# verify that requirements are met
	for requirement in requirements:
		if not user.inventory.filter(item_id=requirement.item_id, qty__gte=requirement.qty).exists():
			raise RuntimeError("Blueprint requirements not met")
	# remove required items
	for requirement in requirements:
		user.profile.remove_inv_item(requirement.item_id, requirement.qty)
	# add newly built item
	user.profile.add_inv_item(blueprint_info.build_id)

def user_save_my_avatar(user, avatar):
	"""
	Save the user's avatar.
	Raise ValueError if the avatar isn't in the correct format.
	"""
	parts = avatar.split("#")
	if user.profile.is_networker:
		if len(parts) != 3:
			raise ValueError
	else:
		if len(parts) != 2:
			raise ValueError
		if parts[0] != "0":
			raise ValueError
	avatar_data = parts[1].split(",")
	if len(avatar_data) != 14:
		raise ValueError

	user.profile.avatar = parts[0]+"#"+parts[1]
	user.profile.save()

def user_save_my_statements(user, statements):
	"""
	Save the "About me" statements of a user.
	Raise ValueError if the number of statements is not correct.
	"""
	if len(statements) != 6:
		raise ValueError("Incorrect number of statements")
	provided = set()
	for question, answer in statements:
		provided.add(question)
		if not Answer.objects.filter(id=answer, question_id=question).exists():
			raise ValueError("Answer %i is not an answer to Question %i" % (answer, question))
	if len(provided) != 6:
		raise ValueError("Duplicate questions provided")
	mandatory = set(q.id for q in Question.objects.filter(mandatory=True))
	mandatory_provided = mandatory & provided
	if mandatory_provided != mandatory:
		raise ValueError("Mandatory questions %s not provided" % (mandatory - mandatory_provided))
	i = 0
	for question, answer in statements:
		setattr(user.profile, "statement_%s_question_id" % i, question)
		setattr(user.profile, "statement_%s_answer_id" % i, answer)
		i += 1
	user.profile.save()
