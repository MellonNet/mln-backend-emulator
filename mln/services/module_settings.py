from .inventory import remove_inv_item

def create_or_update(cls, module, attrs):
	save_obj, created = cls.objects.get_or_create(module=module, defaults=attrs)
	if not created:
		for key, value in attrs.items():
			setattr(save_obj, key, value)
		save_obj.save()

def get_or_create_module(user, instance_id, item_id):
	if instance_id is not None:
		return user.modules.get(id=instance_id)
	remove_inv_item(user, item_id)
	return user.modules.create(item_id=item_id)
