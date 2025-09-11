from django.core.exceptions import ObjectDoesNotExist

def has_item(user, item_id):
	try:
		user.inventory.filter(item_id=item_id).get()
		return True
	except ObjectDoesNotExist:
		return False

def get_or_none(cls, is_relation=False, *args, **kwargs):
	"""Get a model instance according to the filters, or return None if no matching model instance was found."""
	try:
		if is_relation:
			return cls.get(*args, **kwargs)
		else:
			return cls.objects.get(*args, **kwargs)
	except ObjectDoesNotExist:
		return None
