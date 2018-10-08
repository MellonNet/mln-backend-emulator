from django.urls import reverse

from mln.models.static import MLNError
from mln.tests.models.test_profile import one_user
from mln.tests.setup_testcase import TestCase
from mln.tests.views.api.xml.handler_testcase import req_resp
from mln.views.api.xml.webservice import _webservice_unencrypted, handlers

def raise_mln_error(user, request):
	raise MLNError(MLNError.OPERATION_FAILED)

handlers["RaiseMLNError"] = raise_mln_error

class WebserviceTest(TestCase, metaclass=req_resp):
	SETUP = one_user,
	DIR = "webservice"
	TESTS = "unhandled_request_type", "raise_mln_error"

class WebserviceEncryptionTest(TestCase):
	SETUP = one_user,

	def test_webservice(self):
		# MessageList request
		data = "DBdVUQFVQxEQWUlQDB1HOQwSHA8KCShZFkQCVB8O"
		# Empty message list
		expected = b"DFpITRgQRgBCXllPBx1HRUdRTU4IAgdfAVlOEw0SMGRrHRhLABYACA8LDwEDClVYEk4bEhBaDhFCRRpQChoaBE8aFBwBDUd9RQdDUQJVYVlTHQJFSlUTCh0YABAOWV1FB0NRAlVeDhxGTQAHGgAICx5SWB8XVVMBXERbDAJCRRpQChoaBFE="
		self.client.force_login(self.user)
		response = self.client.post(reverse("webservice"), {"input": data}).content
		self.assertEqual(response, expected)
