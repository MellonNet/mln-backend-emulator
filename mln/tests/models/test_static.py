from mln.models.static import BlueprintInfo, BlueprintRequirement, Color, ItemInfo, ItemType, MessageBody, MessageBodyCategory, MessageTemplate, MessageTemplateAttachment, NetworkerReply, StartingStack
from mln.tests.setup_testcase import cls_setup, requires
from mln.tests.models.dupe_testcase import DupeTest

@cls_setup
def color(cls):
	cls.COLOR_ID = Color.objects.create(color=0).id

@cls_setup
def item(cls):
	cls.ITEM_ID = ItemInfo.objects.create(name="Test Item", type=ItemType.ITEM).id

@cls_setup
def masterpiece(cls):
	cls.MASTERPIECE_ITEM_ID = ItemInfo.objects.create(name="Masterpiece Item", type=ItemType.MASTERPIECE).id

@cls_setup
@requires(item)
def blueprint_info(cls):
	cls.BLUEPRINT_ID = ItemInfo.objects.create(name="Test Item Blueprint", type=ItemType.BLUEPRINT).id
	BlueprintInfo.objects.create(item_id=cls.BLUEPRINT_ID, build_id=cls.ITEM_ID)

@cls_setup
@requires(masterpiece)
def masterpiece_blueprint_info(cls):
	cls.MASTERPIECE_BLUEPRINT_ID = ItemInfo.objects.create(name="Test Masterpiece Blueprint", type=ItemType.BLUEPRINT).id
	BlueprintInfo.objects.create(item_id=cls.MASTERPIECE_BLUEPRINT_ID, build_id=cls.MASTERPIECE_ITEM_ID)

@cls_setup
@requires(blueprint_info)
def blueprint_req(cls):
	cls.REQUIREMENT_ID = ItemInfo.objects.create(name="Requirement", type=ItemType.ITEM).id
	BlueprintRequirement.objects.create(blueprint_item_id=cls.BLUEPRINT_ID, item_id=cls.REQUIREMENT_ID, qty=1)

@cls_setup
@requires(masterpiece_blueprint_info)
def masterpiece_blueprint_req(cls):
	cls.MASTERPIECE_REQUIREMENT_ID = ItemInfo.objects.create(name="Masterpiece Requirement", type=ItemType.ITEM).id
	BlueprintRequirement.objects.create(blueprint_item_id=cls.MASTERPIECE_BLUEPRINT_ID, item_id=cls.MASTERPIECE_REQUIREMENT_ID, qty=1)

@cls_setup
def body_category(cls):
	cls.BODY_CAT_ID = MessageBodyCategory.objects.create(name="Test Category", hidden=False, background_color=0, button_color=0, text_color=0).id

@cls_setup
@requires(body_category)
def body(cls):
	cls.BODY = MessageBody.objects.create(category_id=cls.BODY_CAT_ID, subject="Test Body", text="Test Body")

@cls_setup
@requires(body)
def message_template(cls):
	cls.TEMPLATE_ID = MessageTemplate.objects.create(body=cls.BODY).id

@cls_setup
@requires(message_template, item)
def message_template_attachment(cls):
	MessageTemplateAttachment.objects.create(template_id=cls.TEMPLATE_ID, item_id=cls.ITEM_ID, qty=1)

@cls_setup
@requires(item)
def starting_stack(cls):
	StartingStack.objects.create(item_id=cls.ITEM_ID, qty=10)

class DuplicateItemInfo(DupeTest):
	SETUP = item,

class DuplicateBlueprintRequirement(DupeTest):
	SETUP = blueprint_req,

class DuplicateMessageTemplateAttachment(DupeTest):
	SETUP = message_template_attachment,

class DuplicateStartingStack(DupeTest):
	SETUP = starting_stack,
