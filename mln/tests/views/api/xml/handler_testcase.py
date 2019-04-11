"""Common code for tests that send in a request and compare the response to an expected one, to test request parsing and response generation."""
import os.path

from mln.views.api.xml.webservice import _webservice_unencrypted

VOID_XML = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?><response type="%s" ><result></result></response>'

def _test_req_resp(self, name, is_void):
	with open(os.path.join(self.res, name+"_req.xml")) as file:
		request = file.read()
	response = _webservice_unencrypted(self.user, request)
	if is_void:
		start_index = request.index("type=\"")+6
		request_type = request[start_index:request.index("\"", start_index)]
		expected = VOID_XML % request_type
	else:
		#with open(os.path.join(self.res, name+"_resp.xml"), "w") as file:
		#	file.write(response)
		with open(os.path.join(self.res, name+"_resp.xml")) as file:
			expected = file.read()
	self.assertEqual(response, expected)

def req_resp(name, bases, attrs):
	"""
	Metaclass for request-response testing testcases.
	To use this metaclass, your class must have the attribute "DIR", which should specify the path to the test request and response files (relative to the res folder).
	Your class should also have at least one of TESTS or VOID_TESTS.
	Both TESTS and VOID_TESTS are a list of strings specifying the files used for a test. The request file should be suffixed with _req.xml, the response file with _resp.xml. The string in TESTS should only be the prefix, the suffixes are added automatically.
	Because a lot of requests don't return a result ("void return type"), there is a way of specifying tests for these requests without having to specify a response file. To do so, specify the string in VOID_TESTS instead of TESTS. The response will be automatically checked against the void response string instead of file contents.
	"""
	attrs["res"] = os.path.normpath(os.path.join(__file__, "..", "res", attrs["DIR"]))
	if "TESTS" in attrs:
		for name in attrs["TESTS"]:
			attrs["test_%s" % name] = (lambda name: lambda self: _test_req_resp(self, name, False))(name)
	if "VOID_TESTS" in attrs:
		for name in attrs["VOID_TESTS"]:
			attrs["test_%s" % name] = (lambda name: lambda self: _test_req_resp(self, name, True))(name)
	return type(name, bases, attrs)
