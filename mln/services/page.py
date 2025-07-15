from django.db.transaction import atomic

from mln.models import *
from .inventory import add_inv_item, remove_inv_item

@atomic
def page_save_layout(user, modules):
	"""
	Save the layout of the user's page.
	Delete all modules of the user that aren't in the list of modules to be saved.
	Create new modules or update their position on the page.
	Raise ValueError if a supplied position is out of range.
	Raise RuntimeError if there is already a module at the supplied position.
	"""
	present_ids = []
	for instance_id, item_id, pos_x, pos_y in modules:
		if instance_id is not None:
			present_ids.append(instance_id)
	# if a module is not in the supplied list of modules it was removed and should be deleted
	removed_modules = user.modules.exclude(id__in=present_ids)
	if not user.profile.is_networker:
		for module in removed_modules.all():
			if module.is_setup:
				module.teardown()
			add_inv_item(user, module.item_id)
	removed_modules.delete()

	# Handle swaps: first set every module's position to None, then re-set in the right places
	for instance_id, item_id, pos_x, pos_y in modules:
		if instance_id is None: continue  # a module that is being created won't cause issues
		module = user.modules.get(id=instance_id)
		module.pos_x = None
		module.pos_y = None
		module.save()

	# todo: database info on how wide modules are, improved overlapping checks based on that info
	for instance_id, item_id, pos_x, pos_y in modules:
		if instance_id is not None:
			module = user.modules.get(id=instance_id)
			modified = False
			if pos_x != module.pos_x:
				module.pos_x = pos_x
				modified = True
			if pos_y != module.pos_y:
				module.pos_y = pos_y
				modified = True
			if modified:
				module.save()
		else:
			if not user.profile.is_networker:
				remove_inv_item(user, item_id)
			user.modules.create(item_id=item_id, pos_x=pos_x, pos_y=pos_y)
