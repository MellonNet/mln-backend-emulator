
def create_or_update(cls, module, attrs):
	save_obj, created = cls.objects.get_or_create(module=module, defaults=attrs)
	if not created:
		for key, value in attrs.items():
			setattr(save_obj, key, value)
		save_obj.save()
