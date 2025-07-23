from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q

from ..models.static import ItemInfo, ItemType

def add_inv_item(user, item_id, qty=1):
	"""
	Add one or more items to the user's inventory.
	Always use this function instead of creating InventoryStacks directly.
	This function creates a stack only if it does not already exist, and otherwise adds to the existing stack.
	- If this is the first time the user has obtained this item, it will also trigger the first_obtained_item message (if applicable).
	"""
	try:
		stack = user.inventory.get(item_id=item_id)
		stack.qty += qty
		stack.save()
		return stack
	except ObjectDoesNotExist:
		stack = user.inventory.create(item_id=item_id, qty=qty)
		from .message import first_obtained_item
		first_obtained_item(user, item_id)
		return stack

def remove_inv_item(user, item_id, qty=1):
	"""
	Remove one or more items from the user's inventory.
	Always use this function instead of modifying InventoryStacks directly.
	This function subtracts the number of items from the stack, and deletes the stack if no more items are left.
	- Raise RuntimeError if the stack to remove items from does not exist, or if it has fewer items than should be removed.
	"""
	try:
		stack = user.inventory.get(item_id=item_id)
	except ObjectDoesNotExist:
		raise RuntimeError("No stack of item ID %i of user %s exists to delete from" % (item_id, user))
	if stack.qty > qty:
		stack.qty -= qty
		stack.save()
	elif stack.qty == qty:
		stack.delete()
	else:
		raise RuntimeError("%s has fewer items than the %i requested to delete" % (stack, qty))

def refund_invalid_modules(user):
	corrupt_modules = user.modules.filter(Q(pos_x__isnull=True) | Q(pos_y__isnull=True))
	for module in corrupt_modules:
		add_inv_item(user, module.item_id)
	corrupt_modules.delete()

def assert_has_item(user, item_id, qty=1, field_name=None):
	"""
	Raise ValidationError if the user has less than qty items in their inventory.
	- Never raises an error for networkers.
	"""
	if user.profile.is_networker:
		# networkers can do anything without needing items
		return
	if not user.inventory.filter(item_id=item_id, qty__gte=qty).exists():
		if qty == 1:
			message = "User does not have item %s" % ItemInfo.objects.get(id=item_id)
		else:
			message = "User does not have at least %i of item %s" % (qty, ItemInfo.objects.get(id=item_id))
		if field_name is not None:
			raise ValidationError({field_name: message})
		raise ValidationError(message)

def has_item(user, item_id):
	try:
		user.inventory.filter(item_id=item_id).get()
		return True
	except ObjectDoesNotExist:
		return False

def get_badges(user):
	return user.inventory.filter(item__type=ItemType.BADGE)
