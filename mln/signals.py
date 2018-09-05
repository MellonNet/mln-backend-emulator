"""Module for signal handlers."""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models.dynamic import Profile
from .models.static import StartingStack

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	"""Add a profile for user data, as well as MLN's starting items, when a user is created."""
	if created:
		profile = Profile.objects.create(user=instance)
		for stack in StartingStack.objects.all():
			profile.add_inv_item(stack.item_id, stack.qty)
