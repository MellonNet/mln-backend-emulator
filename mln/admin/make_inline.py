from django.contrib import admin

inlines = set()
custom = {}

def _make_inlines(*inlinees):
	"""Create admin inline classes for models."""
	inline_classes = {}
	for inlinee in inlinees:
		attrs = {"extra": 0}
		if isinstance(inlinee, tuple):
			attrs.update(inlinee[1])
			inlinee = inlinee[0]
		attrs["model"] = inlinee
		Inlinee = type("Inlinee", (admin.TabularInline,), attrs)

		inline_classes.setdefault(inlinee, []).append(Inlinee)
		inlines.add(inlinee)
	return inline_classes

def make_inline(inliner, *inlinees, get_inlines=None):
	"""
	Create the main model's inline class as well as inline classes for the models to be inlined.
	The optional get_inlines parameter specifies which inlines to display for a specific object.
	The default is to display all inlines for all objects.
	"""
	inline_classes = _make_inlines(*inlinees)
	class InlinerAdmin(admin.ModelAdmin):
		inlines = [x for i in inline_classes.values() for x in i]
		if get_inlines is not None:
			def get_inline_instances(self, request, obj=None):
				if obj is not None:
					for inline in get_inlines(obj):
						for cls in inline_classes[inline]:
							yield cls(self.model, self.admin_site)

		class Media:
			css = { "all": ("admin/inlines.css",) }

	custom[inliner] = InlinerAdmin
	return InlinerAdmin
