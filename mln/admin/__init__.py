"""
Config for displaying MLN's models in the django admin.
Most of the code here is for displaying various settings models inline with the model admin interface they correspond to, for example showing blueprint requirements for a blueprint item.
"""
from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.admin.helpers import ActionForm
from django.db.models import Q

from ..models.dynamic import Attachment, Friendship, Message, Profile, InventoryStack
from ..models.dynamic.module import Module, module_settings_classes, ModuleSaveConcertArcade, ModuleSaveSoundtrack
from ..models.dynamic.module_settings_arcade import DeliveryArcadeTile
from ..models.static import Answer, BlueprintInfo, BlueprintRequirement, ItemInfo, ItemType, MessageBody, MessageBodyType, MessageTemplate, MessageTemplateAttachment, ModuleEditorType, ModuleHarvestYield, ModuleInfo, ModuleSetupCost, NetworkerFriendshipCondition, NetworkerFriendshipConditionSource, NetworkerMessageTriggerLegacy, NetworkerMessageAttachmentLegacy, NetworkerReply, StartingStack, Question
from ..models.static.module_handlers import ModuleExecutionCost, ModuleGuestYield, ModuleMessage, ModuleOwnerYield
from .make_inline import custom, inlines, make_inline

# Normal but customized admin interfaces

class ProfileAdmin(admin.ModelAdmin):
	list_display = "user", "rank", "is_networker"
	search_fields = "user__username",
	list_filter = "rank", "is_networker"

custom[Profile] = ProfileAdmin

class FriendshipAdmin(admin.ModelAdmin):
	list_display = "from_user", "to_user", "status"
	list_display_links = "from_user", "to_user"
	search_fields = "from_user__username", "to_user__username"
	list_filter = "status",

custom[Friendship] = FriendshipAdmin

# ----- MessageBody -----

MBT = MessageBodyType
has_handler = lambda msg: (
	msg.type in {MBT.USER, MBT.SYSTEM, MBT.BETA, MBT.INTEGRATION, MBT.UNPUBLISHED, MBT.OTHER} or  # unsupported
	(msg.type == MBT.FRIEND and NetworkerFriendshipCondition.objects.filter(Q(success_body=msg) | Q(failure_body=msg)).exists()) or
	(msg.type in [MBT.REPLY, MBT.ITEM] and NetworkerReply.objects.filter(template__body=msg).exists()) or
	(msg.type == MBT.MODULE and ModuleMessage.objects.filter(message__body=msg).exists())
)

has_handler.short_description = "has handler"
has_handler.boolean = True

class HasHandlerFilter(admin.SimpleListFilter):
	title = 'handler'
	parameter_name = "handler"
	default_value = None

	def lookups(self, request, model_admin):
		"""Returns a list of (URL id, human-readable name)."""
		return [("true", "Has handler"), ("false", "No handler")]

	def queryset(self, request, queryset):
		"""Returns a queryset of messages that match the requested handler status"""
		if self.value() is None: return queryset
		messages = [msg.id for msg in queryset.all() if has_handler(msg) == (self.value() == "true")]
		return queryset.filter(id__in=messages)

class MessageBodyTypeForm(ActionForm):
	"""Allows the user to pick a MessageBodyType before performing an action."""
	type = forms.ChoiceField(choices=[(name, name.lower()) for name in MBT.__members__.keys()])

class MessageBodyAdmin(admin.ModelAdmin):
	list_display = "subject", "text", "type", has_handler
	search_fields = "subject", "text"
	filter_vertical = "easy_replies",
	list_filter = "type", HasHandlerFilter, "category"
	action_form = MessageBodyTypeForm
	actions = ["change_type"]

	@admin.action(description="Change message type")
	def change_type(self, request, queryset):
		type_str = request.POST["type"]
		type_ = MessageBodyType[type_str]
		queryset.update(type=type_)

custom[MessageBody] = MessageBodyAdmin

# ----- End of MessageBody -----

class DeliveryArcadeTileAdmin(admin.ModelAdmin):
	list_display = "module", "tile_id", "x", "y"

custom[DeliveryArcadeTile] = DeliveryArcadeTileAdmin

class StackAdmin(admin.ModelAdmin):
	list_display = "qty", "item"
	list_display_links = "item",
	search_fields = "item__name",
	list_filter = "item__type",

custom[StartingStack] = StackAdmin

class InventoryStackAdmin(StackAdmin):
	list_display = ("owner",) + StackAdmin.list_display
	search_fields = ("owner__username",) + StackAdmin.search_fields

custom[InventoryStack] = InventoryStackAdmin

# Inline display functions

def get_item_info_inlines(obj):
	if obj.type == ItemType.BLUEPRINT:
		yield BlueprintInfo
		yield BlueprintRequirement
	elif obj.type == ItemType.MODULE:
		yield ModuleInfo
		yield ModuleHarvestYield
		yield ModuleGuestYield
		yield ModuleOwnerYield
		yield ModuleMessage
		if obj.module_info.editor_type not in (ModuleEditorType.LOOP_SHOPPE, ModuleEditorType.NETWORKER_TRADE, ModuleEditorType.STICKER_SHOPPE, ModuleEditorType.TRADE):
			yield ModuleSetupCost
		if obj.module_info.is_executable:
			yield ModuleExecutionCost

def get_settings_inlines(obj):
	inlines = obj.get_settings_classes()
	if inlines == (ModuleSaveConcertArcade,):
		yield ModuleSaveConcertArcade
		yield ModuleSaveSoundtrack
	else:
		yield from inlines

# Misc inlines

make_inline(Question, Answer)

message_admin = make_inline(Message, Attachment)
message_admin.list_display = "sender", "recipient", "body", "is_read"
message_admin.list_display_links = "body",
message_admin.list_filter = "is_read",
message_admin.search_fields = "sender__username", "recipient__username", "body__subject", "body__text"

friend_cond_admin = make_inline(NetworkerFriendshipCondition)
friend_cond_admin.list_display = "networker", "condition", "success_body", "failure_body", "source"
friend_cond_admin.list_display_links = "networker",
friend_cond_admin.search_fields = "networker__username", "condition__name", "success_body__subject", "success_body__text", "failure_body__subject", "failure_body__text"

trigger_admin_legacy = make_inline(NetworkerMessageTriggerLegacy, NetworkerMessageAttachmentLegacy)
trigger_admin_legacy.list_display = "networker", "body", "trigger", "source", "notes"
trigger_admin_legacy.list_display_links = "body",
trigger_admin_legacy.search_fields = "networker", "body__subject", "body__text", "trigger", "source", "notes"

message_template_admin = make_inline(MessageTemplate, MessageTemplateAttachment)
message_template_admin.list_display = "body",
message_template_admin.list_display_links = "body",
message_template_admin.search_fields = "body__subject", "body__text"

networker_reply_admin = make_inline(NetworkerReply, NetworkerMessageTriggerLegacy)
networker_reply_admin.networker = lambda _, reply: reply.template.networker
networker_reply_admin.networker.short_description = "Networker"
networker_reply_admin.trigger = lambda _, reply: reply.trigger_attachment or reply.trigger_body
networker_reply_admin.trigger.short_description = "Trigger"
networker_reply_admin.response = lambda _, reply: reply.template.body.subject
networker_reply_admin.response.short_description = "Response"
networker_reply_admin.attachment = lambda _, reply: next(iter(reply.template.attachments.all()), None)
networker_reply_admin.attachment.short_description = "Attachment"
networker_reply_admin.list_display = "networker", "trigger", "response", "attachment", "trigger_item_obtained"
networker_reply_admin.list_display_links = "response",
networker_reply_admin.search_fields = "networker__username", "template__attachments__item__name",  "template__body__subject", "template__body__text", "trigger_attachment__name", "trigger_body__subject", "trigger_body__text", "trigger_item_obtained__name"

# Item infos

item_info_admin = make_inline(ItemInfo, ModuleInfo, (ModuleGuestYield, {"fk_name": "module_item"}), (ModuleOwnerYield, {"fk_name": "module_item"}), ModuleMessage, (ModuleExecutionCost, {"fk_name": "module_item"}), (ModuleSetupCost, {"fk_name": "module_item"}), (ModuleHarvestYield, {"fk_name": "item"}), (BlueprintInfo, {"fk_name": "item"}), (BlueprintRequirement, {"fk_name": "blueprint_item"}), get_inlines=get_item_info_inlines)
item_info_admin.list_display = "name", "type"
item_info_admin.search_fields = "name",
item_info_admin.list_filter = "type",

# Modules & module settings

settings = set()
for classes in module_settings_classes.values():
	for cls in classes:
		settings.add(cls)

module_admin = make_inline(Module, *settings, get_inlines=get_settings_inlines)
module_admin.list_display = "owner", "item", "pos_x", "pos_y", "total_clicks"
module_admin.list_display_links = "item",
module_admin.search_fields = "owner__username", "item__name"

# Register admin interfaces

for model in apps.get_app_config("mln").get_models():
	if model in custom:
		admin.site.register(model, custom[model])
	elif model not in inlines:
		admin.site.register(model)
