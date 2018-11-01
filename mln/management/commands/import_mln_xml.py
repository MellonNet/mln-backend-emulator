import xml.etree.ElementTree as et

from django.core.management.base import BaseCommand

from mln.models.static import Answer, ArcadePrize, BlueprintInfo, BlueprintRequirement, Color, ItemInfo, ItemType, MessageBody, ModuleEditorType, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleSkin, ModuleYieldInfo, StartingStack, Question

href_types = {
	"download3C08891ADDFAF741ECF73F38FB40B2A3":   ModuleEditorType.CONCERT_I_ARCADE,
	"download124C900AD0613F3B0E8683473AC6B267":   ModuleEditorType.CONCERT_II_ARCADE,
	"download7BBDE1968863AF36A4723D79CEBE817E":   ModuleEditorType.DELIVERY_ARCADE,
	"download6308BE1BFE39A4E7A3ADC4D112807016":   ModuleEditorType.DESTRUCTOID_ARCADE,
	"download65E88EEE1750F1FF25361D8A52651BF1":   ModuleEditorType.DR_INFERNO_ROBOT_SIM,
	"upload94145C71-2215-40F4-BC55-705F8CA24ACA": ModuleEditorType.FACTORY_GENERIC,
	"upload6FE45D31-426C-41DC-96F0-04C16BDAC640": ModuleEditorType.FACTORY_NON_GENERIC,
	"upload5E54C1F7-9D69-4089-A28B-C9A6054C2482": ModuleEditorType.FRIEND_SHARE,
	"download8D2D8E39CFEEF2BE409F2557F48F810C":   ModuleEditorType.FRIENDLY_FELIX_CONCERT,
	"upload6BE2047F-A1E7-46FE-ABE9-CD910C6EF59D": ModuleEditorType.GALLERY_GENERIC,
	"uploadE79A5782-F4CC-4FA6-B71B-5266E2830236": ModuleEditorType.GALLERY_NON_GENERIC,
	"upload5F35F258-650A-46E6-A4F3-07C4823F51EA": ModuleEditorType.GENERIC,
	"uploadBD27CDD3-01AB-4A14-B065-44AD7295987F": ModuleEditorType.GROUP_PERFORMANCE,
	"download16F9FFF4A1719FF27AA4E4BD59ACAC27":   ModuleEditorType.HOP_ARCADE,
	"upload2ADB5931-F7EE-4363-9AFB-EBA8E45C6FB8": ModuleEditorType.LOOP_SHOPPE,
	"uploadC85FF476-57A7-41EE-BA1A-45D259F438A8": ModuleEditorType.NETWORKER_TEXT,
	"upload66F5B629-AEB6-4C04-B56C-BC1BCA22ABF5": ModuleEditorType.NETWORKER_TRADE,
	"uploadD668BCBE-4B58-406B-91C8-3C09AC4216DF": ModuleEditorType.PLASTIC_PELLET_INDUCTOR,
	"upload3B10831D-FEBE-4C44-B964-6D69B49EA1C6": ModuleEditorType.ROCKET_GAME,
	"upload5CD17986-C326-4A56-9094-552F275D5906": ModuleEditorType.SOUNDTRACK,
	"upload617A0D10-FA99-42AA-8B44-6534997F8819": ModuleEditorType.STICKER,
	"upload28814700-1EEA-458C-A494-6C4797739455": ModuleEditorType.STICKER_SHOPPE,
	"uploadB58AC317-A0A2-41C4-8AA7-2086AB69CE9A": ModuleEditorType.TRADE,
	"uploadF10B502A-8D24-43E3-BA33-84C183B5D857": ModuleEditorType.TRIO_PERFORMANCE,
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
