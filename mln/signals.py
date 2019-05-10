"""Module for signal handlers."""
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models.dynamic import Profile
from .models.static import StartingStack
from .services.inventory import add_inv_item

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	"""Add a profile for user data, as well as MLN's starting items, when a user is created."""
	if created:
		profile = Profile.objects.create(user=instance)
		for stack in StartingStack.objects.all():
			add_inv_item(instance, stack.item_id, stack.qty)

@receiver(pre_save)
def pre_save_full_clean_handler(sender, instance, *args, **kwargs):
	"""Force mln models to call full_clean before save."""
	if sender.__module__.startswith("mln"):
		instance.full_clean()
