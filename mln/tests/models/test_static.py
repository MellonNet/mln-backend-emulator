from mln.models.static import BlueprintInfo, BlueprintRequirement, Color, ItemInfo, ItemType, MessageBody, NetworkerMessageAttachment, NetworkerMessageTrigger, StartingStack
from mln.tests.setup_testcase import cls_setup, requires
from mln.tests.models.dupe_testcase import DupeTest

@cls_setup
def color(cls):
	cls.COLOR_ID = Color.objects.create(color=0).id

@cls_setup
def item(cls):
	cls.ITEM_ID = ItemInfo.objects.create(name="Test Item", type=ItemType.ITEM).id

@cls_setup
@requires(item)
def blueprint_info(cls):
	cls.BLUEPRINT_ID = ItemInfo.objects.create(name="Test Item Blueprint", type=ItemType.BLUEPRINT).id
	BlueprintInfo.objects.create(item_id=cls.BLUEPRINT_ID, build_id=cls.ITEM_ID)

@cls_setup
@requires(blueprint_info)
def blueprint_req(cls):
	cls.REQUIREMENT_ID = ItemInfo.objects.create(name="Requirement", type=ItemType.ITEM).id
	BlueprintRequirement.objects.create(blueprint_item_id=cls.BLUEPRINT_ID, item_id=cls.REQUIREMENT_ID, qty=1)

@cls_setup
def body(cls):
	cls.BODY = MessageBody.objects.create(subject="Test Body", text="Test Body")

@cls_setup
@requires(body)
def networker_message_trigger(cls):
	cls.TRIGGER_ID = NetworkerMessageTrigger.objects.create(body=cls.BODY, source="test").id

@cls_setup
@requires(networker_message_trigger, item)
def networker_message_attachment(cls):
	NetworkerMessageAttachment.objects.create(trigger_id=cls.TRIGGER_ID, item_id=cls.ITEM_ID, qty=1)

@cls_setup
@requires(item)
def starting_stack(cls):
	StartingStack.objects.create(item_id=cls.ITEM_ID, qty=10)

class DuplicateItemInfo(DupeTest):
	SETUP = item,

class DuplicateBlueprintRequirement(DupeTest):
	SETUP = blueprint_req,

class DuplicateNetworkerMessageAttachment(DupeTest):
	SETUP = networker_message_attachment,

class DuplicateStartingStack(DupeTest):
	SETUP = starting_stack,
