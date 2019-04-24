from django.core.exceptions import ValidationError

from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.models.dupe_testcase import DupeTest
from mln.tests.models.test_profile import one_user, two_users, user_has_item
from mln.tests.models.test_static import body, item

@setup
@requires(body, two_users)
def message(self):
	self.message = self.user.messages.create(sender=self.other_user, body_id=self.BODY.id)

@setup
@requires(item, message)
def attachment(self):
	self.message.attachments.create(item_id=self.ITEM_ID, qty=1)

class DuplicateAttachment(DupeTest):
	SETUP = attachment,

class DuplicateInventoryStack(DupeTest):
	SETUP = user_has_item,
