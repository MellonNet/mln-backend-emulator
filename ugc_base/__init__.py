import functools

from django.db.models.signals import post_delete, pre_save

"""Automatically delete files from the filesystem when the corresponding is deleted, or the file is updated."""

def _auto_delete_file_on_delete(attr, sender, instance, **kwargs):
	getattr(instance, attr).delete(save=False)

def _auto_delete_file_on_change(attr, sender, instance, **kwargs):
	if not instance.id:
		return False

	try:
		old_file = getattr(sender.objects.get(id=instance.id), attr)
	except sender.DoesNotExist:
		return False

	new_file = getattr(instance, attr)
	if not old_file == new_file:
		old_file.delete(save=False)

def clean_file(cls, attr):
	"""Call this function with a model and the name of its file attribute to set up automatic file deletion for this model."""
	post_delete.connect(functools.partial(_auto_delete_file_on_delete, attr), sender=cls, weak=False)
	pre_save.connect(functools.partial(_auto_delete_file_on_change, attr), sender=cls, weak=False)
