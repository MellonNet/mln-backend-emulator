from enum import auto, Enum
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db import models
from django.db.models import Q

DAY = timedelta(days=1)

class EnumField(models.PositiveSmallIntegerField):
	def __init__(self, enum, *args, **kwargs):
		self.enum = enum
		super().__init__(*args, choices=[(member, member.name.lower().replace("_", " ")) for member in enum], **kwargs)

	def deconstruct(self):
		name, path, args, kwargs = super().deconstruct()
		args = self.enum, *args
		del kwargs["choices"]
		return name, path, args, kwargs

	def from_db_value(self, value, expression, connection):
		if value is None:
			return None
		return self.enum(value)

	def get_prep_value(self, value):
		if value is None:
			return None
		if isinstance(value, str):
			return self.enum[value[value.index(".")+1:]].value
		return value.value

	def to_python(self, value):
		if value is None:
			return None
		if isinstance(value, str):
			return self.enum[value[value.index(".")+1:]]
		return value

def get_or_none(cls, *args, **kwargs):
	"""Get a model instance according to the filters, or return None if no matching model instance was found."""
	try:
		return cls.objects.get(*args, **kwargs)
	except ObjectDoesNotExist:
		return None
