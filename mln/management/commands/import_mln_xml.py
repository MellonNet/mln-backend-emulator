import xml.etree.ElementTree as et

from django.core.management.base import BaseCommand

from mln.models.static import Answer, BlueprintInfo, BlueprintRequirement, Color, ItemInfo, ItemType, MessageBody, MessageBodyCategory, MessageTemplate, MessageTemplateAttachment, ModuleEditorType, ModuleExecutionCost, ModuleGuestYield, ModuleHarvestYield, ModuleInfo, ModuleMessage, ModuleOwnerYield, ModuleSetupCost, ModuleSkin, StartingStack, Question

href_types = {
	"Concert I Arcade Game": ModuleEditorType.CONCERT_I_ARCADE,
	"Concert II Arcade Game": ModuleEditorType.CONCERT_II_ARCADE,
	"Delivery Arcade Game": ModuleEditorType.DELIVERY_ARCADE,
	"Destructoid Arcade Game": ModuleEditorType.DESTRUCTOID_ARCADE,
	"Dr- Infernos Robot Simulator Module": ModuleEditorType.DR_INFERNO_ROBOT_SIM,
	"Factory": ModuleEditorType.FACTORY_GENERIC,
	"Factory (Static Background)": ModuleEditorType.FACTORY_NON_GENERIC,
	"Friend Share": ModuleEditorType.FRIEND_SHARE,
	"Friendly Felixs Concert Module": ModuleEditorType.FRIENDLY_FELIX_CONCERT,
	"Gallery": ModuleEditorType.GALLERY_GENERIC,
	"Gallery (Static Background)": ModuleEditorType.GALLERY_NON_GENERIC,
	"Generic": ModuleEditorType.GENERIC,
	"Group Performance Module": ModuleEditorType.GROUP_PERFORMANCE,
	"Hop Arcade Game": ModuleEditorType.HOP_ARCADE,
	"Loop Shoppe": ModuleEditorType.LOOP_SHOPPE,
	"Networker Text": ModuleEditorType.NETWORKER_TEXT,
	"Trade (Networker)": ModuleEditorType.NETWORKER_TRADE,
	"Pellet Inductor": ModuleEditorType.PLASTIC_PELLET_INDUCTOR,
	"Rocket Game Module": ModuleEditorType.ROCKET_GAME,
	"Soundtrack Module": ModuleEditorType.SOUNDTRACK,
	"Sticker": ModuleEditorType.STICKER,
	"Sticker Shoppe": ModuleEditorType.STICKER_SHOPPE,
	"Trade Module": ModuleEditorType.TRADE,
	"Trio Performance Module": ModuleEditorType.TRIO_PERFORMANCE,
}

class Command(BaseCommand):
	help = "Initialize the DB from the data in the MLN XML file."

	def add_arguments(self, parser):
		parser.add_argument("path")

	def handle(self, *args, **options):
		EasyReply = MessageBody.easy_replies.through
		tables = ItemInfo, BlueprintInfo, BlueprintRequirement, MessageTemplate, MessageTemplateAttachment, ModuleInfo, ModuleExecutionCost, ModuleGuestYield, ModuleHarvestYield, ModuleMessage, ModuleOwnerYield, ModuleSetupCost, MessageBodyCategory, MessageBody, EasyReply, Question, Answer, Color, ModuleSkin, StartingStack
		t = {}
		for table in tables:
			t[table] = []

		xml = et.parse(options["path"])

		for category in xml.findall("messages/category"):
			category_id = int(category.get("id"))
			name = category.get("name")
			hidden = category.get("hidden") is not None
			background_color = int(category.get("Category_Background_Color"), 16)
			button_color = category.get("Category_Button_Color").strip()
			button_color = int(button_color, 16) if button_color else 0
			text_color = category.get("Category_Text_Color").strip()
			text_color = int(text_color, 16) if text_color else 0
			t[MessageBodyCategory].append(MessageBodyCategory(id=category_id, name=name, hidden=hidden, background_color=background_color, button_color=button_color, text_color=text_color))

			for body in category:
				id = int(body.get("id"))
				subject = body.get("subject")
				if subject == "":
					continue
				text = body.get("text")
				t[MessageBody].append(MessageBody(id=id, category_id=category_id, subject=subject, text=text))

		MessageBody.objects.update_or_create(id=1, category_id=1, subject="Placeholder", text="This should not appear")
		for body_elem in xml.findall("messages/category/body"):
			from_id = int(body_elem.get("id"))
			for easy_reply in body_elem.findall("easyReplies/easyReply"):
				to_id = int(easy_reply.get("id"))
				t[EasyReply].append(EasyReply(from_messagebody_id=from_id, to_messagebody_id=to_id))


		for item_info in xml.findall("items/item"):
			id = int(item_info.get("id"))
			type = ItemType[item_info.get("type").upper()]
			t[ItemInfo].append(ItemInfo(id=id, name=item_info.get("name"), type=type))

		for item_info in xml.findall("items/item"):
			id = int(item_info.get("id"))
			type = item_info.get("type")

			if type == "blueprint":
				build_id = int(item_info.find("details/builds/item").get("id"))
				t[BlueprintInfo].append(BlueprintInfo(item_id=id, build_id=build_id))
				for requirement_elem in item_info.findall("details/requirements/item"):
					requirement_id = int(requirement_elem.get("id"))
					qty = int(requirement_elem.get("qty"))
					t[BlueprintRequirement].append(BlueprintRequirement(blueprint_item_id=id, item_id=requirement_id, qty=qty))

			elif type == "module":
				is_executable = item_info.get("isExecutable") == "True"
				href = item_info.get("hrefEditor")
				if href is None:
					editor_type = None
				elif item_info.get("name") == "Networker Pic Module":
					editor_type = ModuleEditorType.NETWORKER_PIC
				else:
					editor_type = href_types[href[href.rindex("/")+1:href.rindex(".")]]
				t[ModuleInfo].append(ModuleInfo(item_id=id, is_executable=is_executable, editor_type=editor_type))

				yield_elem = item_info.find("yield")
				if yield_elem is None: continue

				# Harvest info --> ModuleHarvestYield
				yield_item_id = int(yield_elem.get("itemId"))
				if yield_item_id == 0:  # special case for trophy room modules
					continue 
				max_yield = int(yield_elem.get("maxPerDay"))
				yield_per_day = int(yield_elem.get("perDay"))
				clicks_per_yield = int(yield_elem.get("voteAmount"))
				t[ModuleHarvestYield].append(ModuleHarvestYield(item_id=id, yield_item_id=yield_item_id, max_yield=max_yield, yield_per_day=yield_per_day, clicks_per_yield=clicks_per_yield))

				# Guest yield info --> ModuleGuestYield
				for guest_yield in yield_elem.findall("guestYield/items"): 
					probability = 100  # owner yields do have probability, but they're not in the XML
					item_id = int(guest_yield.get("itemID"))
					qty = int(guest_yield.get("qty"))
					t[ModuleGuestYield].append(ModuleGuestYield(module_item_id=id, item_id=item_id, qty=qty, probability=probability))

				# Owner yield info --> ModuleOwnerYield
				for owner_yield in yield_elem.findall("ownerYield/items"): 
					probability = int(owner_yield.get("success", "100"))
					item_id = int(owner_yield.get("itemID"))
					qty = int(owner_yield.get("qty"))
					t[ModuleOwnerYield].append(ModuleOwnerYield(module_item_id=id, item_id=item_id, qty=qty, probability=probability))

				# execution cost info --> ModuleExecutionCost
				for execution_cost in yield_elem.findall("guestCost/items"):
					cost_item_id = int(execution_cost.get("itemID"))
					cost_qty = int(execution_cost.get("qty"))
					t[ModuleExecutionCost].append(ModuleExecutionCost(module_item_id=id, item_id=cost_item_id, qty=cost_qty))

				# setup cost info --> ModuleSetupCost
				for setup_cost in yield_elem.findall("ownerLaunchCost/items"):
					cost_item_id = int(setup_cost.get("itemID"))
					cost_qty = int(setup_cost.get("qty"))
					t[ModuleSetupCost].append(ModuleSetupCost(module_item_id=id, item_id=cost_item_id, qty=cost_qty))

				# Messages (with items) sent to users on the module owner's friendlist
				for friend_yield in yield_elem.findall("friendYield/items"): 
					item_id = int(friend_yield.get("itemID"))
					qty = int(friend_yield.get("qty"))
					probability = 100  # not in the XML data
					# We need to explicitly check for duplicates here because we create a new MessageTemplate otherwise.
					# There is no other way to detect if a MessageTemplate is being used for a ModuleMessage.
					if ModuleMessage.objects.filter(module_item_id=id).exists(): continue
					message_placeholder = MessageTemplate.objects.create(body_id=1)  # Message body placeholder
					t[MessageTemplate].append(message_placeholder)
					t[MessageTemplateAttachment].append(MessageTemplateAttachment(template_id=message_placeholder.id, item_id=item_id, qty=qty))
					t[ModuleMessage].append(ModuleMessage(module_item_id=id, message_id=message_placeholder.id, probability=probability))

		for question_elem in xml.findall("questions/question"):
			q_id = int(question_elem.get("id"))
			mandatory = question_elem.get("mandatory") == "True"
			t[Question].append(Question(id=q_id, text=question_elem.get("text"), mandatory=mandatory))
			for answer_elem in question_elem.findall("answer"):
				a_id = int(answer_elem.get("id"))
				t[Answer].append(Answer(id=a_id, question_id=q_id, text=answer_elem.get("text")))

		for color in xml.findall("colors/color"):
			id = int(color.get("id"))
			color_id = int(color.find("details").get("color"), 16)
			t[Color].append(Color(id=id, color=color_id))

		for skin in xml.findall("skins/skin"):
			id = int(skin.get("id"))
			name = skin.get("name")
			t[ModuleSkin].append(ModuleSkin(id=id, name=name))

		for xml_stack in xml.findall("startingStacks/stack"):
			item_id = int(xml_stack.get("itemID"))
			qty = int(xml_stack.get("qty"))
			t[StartingStack].append(StartingStack(item_id=item_id, qty=qty))

		for key, value in t.items():
			key.objects.bulk_create(value, ignore_conflicts=True)

		print("Import successful.")
