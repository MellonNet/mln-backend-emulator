"""
Creation lab database/service.
In MLN this can be configured to be a different server, not necessarily the UGC one, which is why I've put it into its own app.
Other than that the creation lab service is very similar to UGC.
"""
from django.apps import AppConfig

class CreationLabConfig(AppConfig):
	name = "creation_lab"
