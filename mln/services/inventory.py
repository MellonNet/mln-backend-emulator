from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q

from mln.models import *

def refund_invalid_modules(user):
	corrupt_modules = user.modules.filter(Q(pos_x__isnull=True) | Q(pos_y__isnull=True))
	for module in corrupt_modules:
		add_inv_item(user, module.item_id)
	corrupt_modules.delete()

def has_item(user, item_id):
	try:
		user.inventory.filter(item_id=item_id).get()
		return True
	except ObjectDoesNotExist:
		return False
