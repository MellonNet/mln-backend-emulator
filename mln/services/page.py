from django.db.transaction import atomic

from mln.models.static import ItemInfo, ItemType

def get_or_create_module(user, instance_id, item_id):
	if instance_id is not None:
		return user.modules.get(id=instance_id)
	if not user.profile.is_networker:
		user.profile.remove_inv_item(item_id)
	return user.modules.create(item_id=item_id, pos_x=0, pos_y=0)

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
			user.profile.add_inv_item(module.item_id)
	removed_modules.delete()

	# todo: database info on how wide modules are, improved overlapping checks based on that info
	for instance_id, item_id, pos_x, pos_y in modules:
		if pos_x < 0 or pos_x > 2:
			raise ValueError("Pos x: %i of module %s (item %i) is out of bounds" % (pos_x, instance_id, item_id))
		if pos_y < 0 or pos_y > 3:
			raise ValueError("Pos y: %i of module %s (item %i) is out of bounds" % (pos_y, instance_id, item_id))
		if user.modules.filter(pos_x=pos_x, pos_y=pos_y).exclude(id=instance_id).exists():
			raise RuntimeError("User already has a module at position %i %i" % (pos_x, pos_y))
		module = get_or_create_module(user, instance_id, item_id)
		module.pos_x = pos_x
		module.pos_y = pos_y
		module.save()

def page_save_options(user, skin_id, color_id, column_color_id):
	"""
	Save page options: page skin, page color, column color.
	Raise RuntimeError if the page skin ID is not the ID of a skin item.
	Raise ValueError if the column color ID is not in the correct range.
	"""
	if skin_id is not None and not ItemInfo.objects.filter(id=skin_id, type=ItemType.SKIN).exists():
		raise RuntimeError("Skin ID %i does not belong to a skin item" % skin_id)
	if column_color_id < 0 or column_color_id > 4:
		raise ValueError("Column Color ID %i does not exist" % column_color_id)
	user.profile.page_skin_id = skin_id
	user.profile.page_color_id = color_id
	user.profile.page_column_color_id = column_color_id
	user.profile.save()
