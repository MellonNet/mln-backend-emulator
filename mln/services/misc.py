from django.core.exceptions import ValidationError

from ..models.static import BlueprintInfo, BlueprintRequirement, ItemInfo, ItemType
from mln.models.dynamic import assert_has_item
from .inventory import add_inv_item, remove_inv_item

from .webhooks import run_rank_webhooks

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
		remove_inv_item(user, requirement.item_id, requirement.qty)
	result = blueprint_info.build
	if result.type == ItemType.MASTERPIECE:
		if user.inventory.filter(item_id=result.id).exists():
			return
		else:
			user.profile.rank += 1
			user.profile.save()
			run_rank_webhooks(user)
	elif result.type == ItemType.BADGE:
		# Running badge webhooks here means they won't run if a badge is just sent
		# Instead we run them in add_inv_item
		if user.inventory.filter(item_id=result.id).exists():
			return

	# add newly built item
	add_inv_item(user, blueprint_info.build_id)
