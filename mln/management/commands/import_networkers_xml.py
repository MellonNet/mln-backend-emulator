import xml.etree.ElementTree as et

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from mln.models.dynamic import Friendship, FriendshipStatus, Profile, InventoryStack
from mln.models.dynamic.module import Module
from mln.models.dynamic.module_settings import ModuleSaveNetworkerPic, ModuleSaveNetworkerText, ModuleSetupTrade, ModuleSaveGeneric
from mln.models.static import Color, ItemInfo, ModuleSkin, MessageBody, NetworkerFriendshipCondition, MessageTemplate, MessageTemplateAttachment, NetworkerReply

module_name_to_type = {
	"banner": 43889,
	"text": 43890,
	"sticker": 56868,
	"loop": 52701,
	"trade": 43884,
	"unknown": 0,
}
message_type_to_body_id = {
	"helprequest": 45222,
	"stickerrequest": 46023,
	"looprequest": 45590,
	"traderequest": 46024,
}


class Command(BaseCommand):
	help = "Import networks to the DB from an XML file."

	def __init__(self):
		super().__init__()
		self.created_objects = {}

	def _store_object(self, table_object):
		table = type(table_object)
		if table not in self.created_objects.keys():
			self.created_objects[table] = []
		self.created_objects[table].append(table_object)
		return table_object

	def add_arguments(self, parser):
		parser.add_argument("path")

	def handle(self, *args, **options):
		xml = et.parse(options["path"])

		for networker in xml.findall("networker"):
			if not User.objects.filter(username=networker.get("name")).exists():
				User.objects.create(username=networker.get("name"))
			user = User.objects.filter(username=networker.get("name")).first()

			background_color_id = 1
			column_color_id = 1
			skin_id = None
			networker_page_data = networker.find("page")
			if networker_page_data is not None:
				background_color_id = int(networker_page_data.get("backgroundColor", "1"))
				column_color_id = int(networker_page_data.get("columnColor", "1"))
				skin_id = networker_page_data.get("skin")

			profile = Profile.objects.filter(user=user).first()
			profile.is_networker = True
			profile.avatar = networker.get("avatar")
			profile.rank = int(networker.get("rank"))
			profile.page_color = Color.objects.filter(id=background_color_id).first()
			profile.page_column_color_id = column_color_id
			if skin_id is not None:
				profile.page_skin = ItemInfo.objects.filter(id=int(skin_id)).first()
			profile.save()

			for friend_data in networker.findall("friends/networker"):
				friend_networker = User.objects.filter(username=friend_data.get("name")).first()
				if friend_networker is not None:
					self._store_object(Friendship(from_user=user, to_user=friend_networker, status=FriendshipStatus.FRIEND))
					self._store_object(Friendship(from_user=friend_networker, to_user=user, status=FriendshipStatus.FRIEND))

			for module_data in networker.findall("modules/module"):
				module_type = module_data.get("type", "unknown").lower()
				module_id = int(module_data.get("id", module_name_to_type[module_type]))
				module_item = ItemInfo.objects.filter(id=module_id).first()

				pos_x = int(module_data.get("x"))
				pos_y = int(module_data.get("y"))
				module = Module.objects.filter(owner=user, pos_x=pos_x, pos_y=pos_y).first()
				if module is not None and module.item != module_item:
					module.delete()
					module = None
				if module is None:
					module = Module.objects.create(item=module_item, owner=user, pos_x=pos_x, pos_y=pos_y, is_setup=True)

				module_skin = None
				module_color = None
				if module_data.get("skin") is not None:
					module_skin = ModuleSkin.objects.filter(id=int(module_data.get("skin"))).first()
				if module_data.get("color") is not None:
					module_color = Color.objects.filter(id=int(module_data.get("color"))).first()
				if module_color is not None or module_skin is not None:
					module_save_generic = ModuleSaveGeneric.objects.filter(module=module).first()
					if module_save_generic is None:
						module_save_generic = ModuleSaveGeneric.objects.create(module=module, skin=module_skin, color=module_color)
					module_save_generic.skin = module_skin
					module_save_generic.color = module_color
					module_save_generic.save()

				if module_type == "banner":
					picture = ItemInfo.objects.filter(id=int(module_data.get("bannerId"))).first()
					module_picture = ModuleSaveNetworkerPic.objects.filter(module=module).first()
					if module_picture is None:
						module_picture = ModuleSaveNetworkerPic.objects.create(module=module, picture=picture)
					module_picture.picture = picture
					module_picture.save()
				elif module_type == "text":
					text = module_data.get("text").replace("\\n", "\n")
					module_text = ModuleSaveNetworkerText.objects.filter(module=module).first()
					if module_text is None:
						module_text = ModuleSaveNetworkerText.objects.create(module=module, text=text)
					module_text.text = text
					module_text.save()
				elif module_type == "sticker" or module_type == "loop" or module_type == "trade":
					give_item = ItemInfo.objects.filter(id=int(module_data.get("giveId"))).first()
					request_item = ItemInfo.objects.filter(id=int(module_data.get("requestId"))).first()
					module_trade = ModuleSetupTrade.objects.filter(module=module).first()
					if module_trade is None:
						module_trade = ModuleSetupTrade.objects.create(module=module, give_item=give_item, give_qty=int(module_data.get("giveQuantity", "1")), request_item=request_item, request_qty=int(module_data.get("requestQuantity")))
					module_trade.give_item = give_item
					module_trade.give_qty = int(module_data.get("giveQuantity", "1"))
					module_trade.request_item = request_item
					module_trade.request_qty = int(module_data.get("requestQuantity"))
					module_trade.save()

			friendship_data = networker.find("friendship")
			if friendship_data is not None:
				condition_item = None
				if friendship_data.get("requiredItem"):
					condition_item = ItemInfo.objects.filter(id=int(friendship_data.get("id"))).first()
				acceptBody = MessageBody.objects.filter(id=int(friendship_data.get("acceptMessageId", "1"))).first()
				declineBody = MessageBody.objects.filter(id=int(friendship_data.get("declineMessageId", "1"))).first()
				self._store_object(NetworkerFriendshipCondition(networker=user, condition=condition_item, success_body=acceptBody, failure_body=declineBody))

			for item_message_trigger_data in networker.findall("messageTriggers/item"):
				trigger_attachment = ItemInfo.objects.filter(id=int(item_message_trigger_data.get("id"))).first()
				if NetworkerReply.objects.filter(networker=user, trigger_attachment=trigger_attachment).exists():
					continue

				message_body = MessageBody.objects.filter(id=item_message_trigger_data.get("responseId")).first()
				message_template = MessageTemplate.objects.create(body=message_body)
				attachment_data = item_message_trigger_data.find("attachment")
				if attachment_data is not None:
					attachment_item = ItemInfo.objects.filter(id=int(attachment_data.get("id"))).first()
					self._store_object(MessageTemplateAttachment(template=message_template, item=attachment_item, qty=int(attachment_data.get("quantity", "1"))))

				self._store_object(NetworkerReply(template=message_template, networker=user, trigger_attachment=trigger_attachment))

			for item_message_trigger_data in networker.findall("messageTriggers/message"):
				trigger_body_id = item_message_trigger_data.get("id", "0")
				if item_message_trigger_data.get("type") is not None:
					trigger_body_id = message_type_to_body_id[item_message_trigger_data.get("type").lower()]

				trigger_body = MessageBody.objects.filter(id=int(trigger_body_id)).first()
				if NetworkerReply.objects.filter(networker=user, trigger_body=trigger_body).exists():
					continue

				message_body = MessageBody.objects.filter(id=item_message_trigger_data.get("responseId")).first()
				message_template = MessageTemplate.objects.create(body=message_body)
				attachment_data = item_message_trigger_data.find("attachment")
				if attachment_data is not None:
					attachment_item = ItemInfo.objects.filter(id=int(attachment_data.get("id"))).first()
					self._store_object(MessageTemplateAttachment(template=message_template, item=attachment_item, qty=int(attachment_data.get("quantity", "1"))))

				self._store_object(NetworkerReply(template=message_template, networker=user, trigger_body=trigger_body))

			for badge_data in networker.findall("badges/badge"):
				badge_item = ItemInfo.objects.filter(id=int(badge_data.get("id"))).first()
				self._store_object(InventoryStack(owner=user, item=badge_item, qty=1))

			print("Imported " + networker.get("name"))

		for key, value in self.created_objects.items():
			key.objects.bulk_create(value, ignore_conflicts=True)
		print("Import complete.")