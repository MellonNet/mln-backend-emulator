"""This module makes it possible to register setup requirements for test cases, and have the setups require other setups as well."""
from django.test import TestCase

_TYPE_CLS_SETUP = 0
_TYPE_SETUP = 1
_type = {}
_deps = {}

class TestCase(TestCase):
	"""
	A test case with a way of declaring setup functions, so that setup code used by multiple test cases can be reused and no inheritance of test cases is necessary.
	Setup functions can either be normal setup functions, which will be run before every test method, or class setup functions, which will be called once before all test methods are called.
	Both normal setup and class setup functions are registered by placing them in the SETUP class variable.
	Setup functions must be decorated with either @setup or @cls_setup, and can optionally be decorated with @requires to declare dependencies to other setup functions.
	The TestCase class recursively resolves setup functions, discarding duplicates, and calls them in the right order.
	"""
	SETUP = ()

	@classmethod
	def setUpTestData(cls):
		cls._cls_setups = []
		cls._setups = []
		cls._add_deps(cls.SETUP)
		for cls_setup in cls._cls_setups:
			cls_setup(cls)
		del cls._cls_setups

	@classmethod
	def _add_deps(cls, deps):
		for dep in deps:
			cls._add_deps(_deps[dep])
			type = _type[dep]
			if type == _TYPE_CLS_SETUP:
				setups = cls._cls_setups
			elif type == _TYPE_SETUP:
				setups = cls._setups
			if dep not in setups:
				setups.append(dep)

	def setUp(self):
		for dep in self._setups:
			dep(self)

def cls_setup(func):
	"""Mark a function as a class setup that will be called once before all the test methods are called."""
	_type[func] = _TYPE_CLS_SETUP
	if func not in _deps:
		_deps[func] = ()
	return func

def setup(func):
	"""Mark a function as a setup that will be called before every test method."""
	_type[func] = _TYPE_SETUP
	if func not in _deps:
		_deps[func] = ()
	return func

def requires(*deps):
	"""Register this setup function to depend on other setups."""
	def decorator(func):
		_deps[func] = deps
		return func
	return decorator
