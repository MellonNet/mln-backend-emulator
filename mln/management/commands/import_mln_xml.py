import xml.etree.ElementTree as et

from django.core.management.base import BaseCommand

from mln.models.static import Answer, ArcadePrize, BlueprintInfo, BlueprintRequirement, Color, ItemInfo, ItemType, MessageBody, ModuleEditorType, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleSkin, ModuleYieldInfo, StartingStack, Question

href_types = {
	"Concert I Arcade Game":   ModuleEditorType.CONCERT_I_ARCADE,
	"Concert II Arcade Game":   ModuleEditorType.CONCERT_II_ARCADE,
	"Delivery Arcade Game":   ModuleEditorType.DELIVERY_ARCADE,
	"Destructoid Arcade Game":   ModuleEditorType.DESTRUCTOID_ARCADE,
	"Dr- Infernos Robot Simulator Module":   ModuleEditorType.DR_INFERNO_ROBOT_SIM,
	"Factory": ModuleEditorType.FACTORY_GENERIC,
	"Factory (Static Background)": ModuleEditorType.FACTORY_NON_GENERIC,
	"Friend Share": ModuleEditorType.FRIEND_SHARE,
	"Friendly Felixs Concert Module":   ModuleEditorType.FRIENDLY_FELIX_CONCERT,
	"Gallery": ModuleEditorType.GALLERY_GENERIC,
	"Gallery (Static Background)": ModuleEditorType.GALLERY_NON_GENERIC,
	"Generic": ModuleEditorType.GENERIC,
	"Group Performance Module": ModuleEditorType.GROUP_PERFORMANCE,
	"Hop Arcade Game":   ModuleEditorType.HOP_ARCADE,
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
		tables = ItemInfo, BlueprintInfo, BlueprintRequirement, ModuleInfo, ModuleYieldInfo, ArcadePrize, ModuleExecutionCost, ModuleSetupCost, MessageBody, EasyReply, Question, Answer, Color, ModuleSkin, StartingStack
		t = {}
		for table in tables:
			t[table] = []

		xml = et.parse(options["path"])

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
				is_setupable = item_info.get("isSetupable") == "True"
				href = item_info.get("hrefEditor")
				if href is None:
					editor_type = None
				elif item_info.get("name") == "Networker Pic Module":
					editor_type = ModuleEditorType.NETWORKER_PIC
				else:
					editor_type = href_types[href[href.rindex("/")+1:href.rindex(".")]]
				t[ModuleInfo].append(ModuleInfo(item_id=id, is_executable=is_executable, is_setupable=is_setupable, editor_type=editor_type))

				yield_elem = item_info.find("yield")
				if yield_elem is not None:
					yield_item_id = int(yield_elem.get("itemId"))
					if yield_item_id == 0:
						continue # weird trophy room
					max_yield = int(yield_elem.get("maxPerDay"))
					yield_per_day = int(yield_elem.get("perDay"))
					clicks_per_yield = int(yield_elem.get("voteAmount"))
					t[ModuleYieldInfo].append(ModuleYieldInfo(item_id=id, yield_item_id=yield_item_id, max_yield=max_yield, yield_per_day=yield_per_day, clicks_per_yield=clicks_per_yield))

					guest_yield = yield_elem.find("guestYield")
					if guest_yield is not None:
						for yield_stack in guest_yield:
							if yield_stack.get("successRate") is None:
								continue
							prize_item_id = int(yield_stack.get("itemID"))
							prize_qty = int(yield_stack.get("qty"))
							success_rate = int(yield_stack.get("successRate"))
							t[ArcadePrize].append(ArcadePrize(module_item_id=id, item_id=prize_item_id, qty=prize_qty, success_rate=success_rate))
					guest_cost = yield_elem.find("guestCost")
					if guest_cost is not None:
						for cost in guest_cost:
							cost_item_id = int(cost.get("itemID"))
							cost_qty = int(cost.get("qty"))
							t[ModuleExecutionCost].append(ModuleExecutionCost(module_item_id=id, item_id=cost_item_id, qty=cost_qty))
					owner_launch_cost = yield_elem.find("ownerLaunchCost")
					if owner_launch_cost is not None:
						for cost in owner_launch_cost:
							cost_item_id = int(cost.get("itemID"))
							cost_qty = int(cost.get("qty"))
							t[ModuleSetupCost].append(ModuleSetupCost(module_item_id=id, item_id=cost_item_id, qty=cost_qty))

		for body in xml.findall("messages/category/body"):
			id = int(body.get("id"))
			subject = body.get("subject")
			if subject == "":
				continue
			text = body.get("text")
			t[MessageBody].append(MessageBody(id=id, subject=subject, text=text))

		for body_elem in xml.findall("messages/category/body"):
			from_id = int(body_elem.get("id"))
			for easy_reply in body_elem.findall("easyReplies/easyReply"):
				to_id = int(easy_reply.get("id"))
				t[EasyReply].append(EasyReply(from_messagebody_id=from_id, to_messagebody_id=to_id))

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
			key.objects.bulk_create(value)

		print("Import successful.")
