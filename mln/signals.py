"""Module for signal handlers."""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models.dynamic import Profile
from .models.static import ItemInfo

def get_id(name):
	return ItemInfo.objects.get(name=name).id

START_ITEMS = [
	# Items
	(get_id("Red LEGO Brick"), 50),
	# Blueprints
	(get_id("Apple Blueprint"), 1),
	(get_id("Trade Module Blueprint"), 1),
	# Modules
	(get_id("Factory Module"), 2),
	(get_id("Gallery Module"), 2),
	(get_id("LEGO Tree Module"), 1),
	(get_id("Soundtrack Module"), 1),
	(43620, 2), # Sticker Module width 3
	(43887, 3), # Sticker Module width 1
	(43888, 3), # Sticker Module width 2
	# Stickers
	(get_id("Fire Truck"), 1),
	(45059, 1), # Creator House
	(get_id("Police Officer"), 1),
	(get_id("Pridak"), 1),
	(get_id("Creator Buggy"), 1),
	# Loops
	(get_id("Electric Guitar 1"), 1),
	(get_id("Hip Hop Drums with Clapping"), 1),
	(get_id("Rock Drums 1"), 1),
	(get_id("Simple Bass 1"), 1),
	(get_id("Simple Bass 2"), 1),
]

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	"""Add a profile for user data, as well as MLN's starting items, when a user is created."""
	if created:
		profile = Profile.objects.create(user=instance)
		for item_id, qty in START_ITEMS:
			profile.add_inv_item(item_id, qty)
