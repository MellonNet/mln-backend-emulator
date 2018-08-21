"""
Config for displaying MLN's models in the django admin.
Most of the code here is for displaying various settings models inline with the model admin interface they correspond to, for example showing blueprint requirements for a blueprint item.
"""
from django.apps import apps
from django.contrib import admin

from .models.dynamic import Attachment, Friendship, Message, Profile, InventoryStack
from .models.module import Module, ModuleSaveConcertArcade, ModuleSaveSoundtrack, module_settings_classes
from .models.static import Answer, ArcadePrize, BlueprintInfo, BlueprintRequirement, ItemInfo, ItemType, MessageBody, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleYieldInfo, Question

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
				for inline in get_inlines(obj):
					for cls in inline_classes[inline]:
						yield cls(self.model, self.admin_site)

	custom[inliner] = InlinerAdmin
	return InlinerAdmin

make_inline(Question, Answer)

def get_item_info_inlines(obj):
	if obj.type == ItemType.BLUEPRINT.value:
		return BlueprintInfo, BlueprintRequirement
	elif obj.type == ItemType.MODULE.value:
		return ModuleInfo, ModuleYieldInfo, ArcadePrize, ModuleExecutionCost, ModuleSetupCost
	else:
		return ()

item_info_admin = make_inline(ItemInfo, ModuleInfo, (ArcadePrize, {"fk_name": "module_item"}), (ModuleExecutionCost, {"fk_name": "module_item"}), (ModuleSetupCost, {"fk_name": "module_item"}), (ModuleYieldInfo, {"fk_name": "item"}), (BlueprintInfo, {"fk_name": "item"}), (BlueprintRequirement, {"fk_name": "blueprint_item"}), get_inlines=get_item_info_inlines)

item_info_admin.list_display = "name", "type"
item_info_admin.search_fields = "name",
item_info_admin.list_filter = "type",

class MessageBodyAdmin(admin.ModelAdmin):
	list_display = "subject", "text"
	search_fields = list_display
	filter_vertical = "easy_replies",

custom[MessageBody] = MessageBodyAdmin

message_admin = make_inline(Message, Attachment)
message_admin.list_display = "sender", "recipient", "body", "is_read"

class InventoryStackAdmin(admin.ModelAdmin):
	list_display = "owner", "qty", "item"
	search_fields = "owner__username", "item__name"
	list_filter = "owner",

custom[InventoryStack] = InventoryStackAdmin

make_inline(Profile, (Friendship, {"fk_name": "to_profile"}), (Friendship, {"fk_name": "from_profile"}))

settings = set()
for classes in module_settings_classes.values():
	for cls in classes:
		settings.add(cls)

def get_settings_inlines(obj):
	inlines = obj.get_settings_classes()
	if inlines == (ModuleSaveConcertArcade,):
		yield ModuleSaveConcertArcade
		yield ModuleSaveSoundtrack
	else:
		yield from inlines

module_admin = make_inline(Module, *settings, get_inlines=get_settings_inlines)
module_admin.list_display = "owner", "item", "pos_x", "pos_y", "total_clicks"
module_admin.list_filter = "owner",

for model in apps.get_app_config("mln").get_models():
	if model in custom:
		admin.site.register(model, custom[model])
	elif model not in inlines:
		admin.site.register(model)
