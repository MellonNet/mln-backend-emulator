from django.apps import AppConfig

class MlnConfig(AppConfig):
	name = "mln"

	def ready(self):
		from . import signals
