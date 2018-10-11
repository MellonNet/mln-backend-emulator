from django.core.exceptions import ValidationError

from ..models.static import BlueprintInfo, BlueprintRequirement, ItemInfo, ItemType

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
	Raise ValidationError if the blueprint is not in the user's inventory.
	Raise RuntimeError if a required item is not in the user's inventory.
	"""
	assert_has_item(user, blueprint_id)
	blueprint_info = BlueprintInfo.objects.get(item_id=blueprint_id)
	requirements = BlueprintRequirement.objects.filter(blueprint_item_id=blueprint_id)
	# remove required items
	for requirement in requirements:
		user.profile.remove_inv_item(requirement.item_id, requirement.qty)
	# add newly built item
	user.profile.add_inv_item(blueprint_info.build_id)

def assert_has_item(user, item_id, qty=1, field_name=None):
	"""Raise ValidationError if the user has less than qty items in their inventory."""
	if not user.inventory.filter(item_id=item_id, qty__gte=qty).exists():
		if qty == 1:
			message = "User %s does not have item %s" % (user, ItemInfo.objects.get(id=item_id))
		else:
			message = "User %s does not have at least %i of item %s" % (user, qty, ItemInfo.objects.get(id=item_id))
		if field_name is not None:
			raise ValidationError({field_name: message})
		raise ValidationError(message)
