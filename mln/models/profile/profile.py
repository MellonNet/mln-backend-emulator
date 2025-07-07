from django.core.validators import MaxValueValidator

from ..utils import *
from ..items import *

from .color import *

class Profile(models.Model):
	"""
	MLN-specific user data.
	This includes the avatar, user rank, available votes, page skin and page colors.
	"""
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	is_networker = models.BooleanField(default=False)
	avatar = models.CharField(max_length=64, default="0#1,6,1,16,5,1,6,13,2,9,2,2,1,1")
	rank = models.PositiveSmallIntegerField(default=0)
	available_votes = models.PositiveSmallIntegerField(default=20)
	last_vote_update_time = models.DateTimeField(default=now)
	page_skin = models.ForeignKey(ItemInfo, null=True, blank=True, related_name="+", on_delete=models.PROTECT, limit_choices_to={"type": ItemType.SKIN})
	page_color = models.ForeignKey(Color, null=True, blank=True, related_name="+", on_delete=models.CASCADE)
	page_column_color_id = models.PositiveSmallIntegerField(null=True, blank=True, validators=(MaxValueValidator(4),)) # hardcoded for some reason

	def __str__(self):
		return self.user.username

	def clean(self):
		if self.avatar != "png":
			parts = self.avatar.split("#")
			if len(parts) not in (2, 3):
				raise ValidationError({"avatar": "Avatar does not have the right number of parts"})
			if (self.is_networker and parts[0] not in ("0", "1")) or (not self.is_networker and parts[0] != "0"):
				raise ValidationError({"avatar": "First part of avatar should not be %s" % parts[0]})
			avatar_data = parts[1].split(",")
			if not((parts[0] == "0" and len(avatar_data) == 14) or (parts[0] == "1" and len(avatar_data) == 5)):
				raise ValidationError({"avatar": "Data part of avatar has %i values but shouldn't %s" % (len(avatar_data), self.avatar)})
			self.avatar = parts[0]+"#"+parts[1]

		max_votes = 20 + 8 * self.rank
		if self.available_votes >	max_votes:
			raise ValidationError({"available_votes": "Can't have more votes available than the maximum of %i at rank %i" % (max_votes, self.rank)})

		if self.page_skin_id is not None:
			assert_has_item(self.user, self.page_skin_id)

	def update_available_votes(self):
		"""
		Calculate how many votes are available.
		Votes regenerate at a rate determined by rank, but will only be updated if you explicitly call this function.
		"""
		time_since_last_update = now() - self.last_vote_update_time
		max_votes = 20 + 8 * self.rank
		new_votes, time_remainder = divmod(time_since_last_update, (DAY / max_votes))
		if new_votes > 0:
			self.available_votes = min(self.available_votes + new_votes, max_votes)
			self.last_vote_update_time = now() - time_remainder
			self.save()
