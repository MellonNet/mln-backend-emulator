"""Module for signal handlers."""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models.dynamic import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	"""Add a profile for user data, as well as MLN's starting items, when a user is created."""
	if created:
		profile = Profile.objects.create(user=instance)
		profile.add_inv_item(45056)
		profile.add_inv_item(45059)
		profile.add_inv_item(45077)
		profile.add_inv_item(43573)
		profile.add_inv_item(43586)
		profile.add_inv_item(43593)
		profile.add_inv_item(43596)
		profile.add_inv_item(43597)
		profile.add_inv_item(43598)
		profile.add_inv_item(43599)
		profile.add_inv_item(43600)
		profile.add_inv_item(53602)
		profile.add_inv_item(43620, qty=2)
		profile.add_inv_item(43876)
		profile.add_inv_item(43887, qty=3)
		profile.add_inv_item(43888, qty=3)
		profile.add_inv_item(45173)
		profile.add_inv_item(43907, qty=2)
		profile.add_inv_item(43911, qty=2)
		profile.add_inv_item(43449, qty=50)
