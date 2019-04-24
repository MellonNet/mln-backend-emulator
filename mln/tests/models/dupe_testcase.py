from django.core.exceptions import ValidationError

from mln.tests.setup_testcase import TestCase

class DupeTest(TestCase):
	def test(self):
		if not self.SETUP:
			return
		with self.assertRaises(ValidationError):
			for setup in self.SETUP:
				setup(self)
