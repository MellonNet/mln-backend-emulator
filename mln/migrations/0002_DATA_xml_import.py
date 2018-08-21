import os.path
import uuid
import xml.etree.ElementTree as et

from django.db import migrations

from mln.handlers.utils import uuid_int
from mln.models.static import Answer, ArcadePrize, BlueprintInfo, BlueprintRequirement, Color, ItemInfo, ItemType, MessageBody, ModuleExecutionCost, ModuleInfo, ModuleSetupCost, ModuleSkin, ModuleYieldInfo, Question
from mln.webservice import decrypt

def import_xml(apps, schema_editor):
	xml = et.parse(os.path.abspath(os.path.join(__file__, "..", "..", "..", "..", "content", "upload", "XMLCache/MLN/MLN_1033_20100211081940.xml")))

	encrypted_xml = et.fromstring(b"<encrypted>"+decrypt(xml.find("encrypted").text)+b"</encrypted>")
	xml.getroot().extend(encrypted_xml)

	for item_info in xml.findall("items/item"):
		id = uuid_int(item_info.get("id"))
		type = ItemType[item_info.get("type").upper()].value
		ItemInfo.objects.create(id=id, name=item_info.get("name"), type=type)

	for item_info in xml.findall("items/item"):
		id = uuid_int(item_info.get("id"))
		type = item_info.get("type")

		if type == "blueprint":
			build_id = uuid_int(item_info.find("details/builds/item").get("id"))
			BlueprintInfo.objects.create(item_id=id, build_id=build_id)
			for requirement_elem in item_info.findall("details/requirements/item"):
				requirement_id = uuid_int(requirement_elem.get("id"))
				qty = int(requirement_elem.get("qty"))
				BlueprintRequirement.objects.create(blueprint_item_id=id, item_id=requirement_id, qty=qty)

		elif type == "module":
			is_executable = item_info.get("isExecutable") == "True"
			is_setupable = item_info.get("isSetupable") == "True"
			href_editor = item_info.get("hrefEditor")
			ModuleInfo.objects.create(item_id=id, is_executable=is_executable, is_setupable=is_setupable, href_editor=href_editor)

			yield_elem = item_info.find("yield")
			if yield_elem is not None:
				yield_item_id = uuid_int(yield_elem.get("itemId"))
				if yield_item_id == 0:
					continue # weird trophy room
				max_yield = int(yield_elem.get("maxPerDay"))
				yield_per_day = int(yield_elem.get("perDay"))
				clicks_per_yield = int(yield_elem.get("voteAmount"))
				ModuleYieldInfo.objects.create(item_id=id, yield_item_id=yield_item_id, max_yield=max_yield, yield_per_day=yield_per_day, clicks_per_yield=clicks_per_yield)

				guest_yield = yield_elem.find("guestYield")
				if guest_yield is not None:
					for yield_stack in guest_yield:
						if yield_stack.get("successRate") is None:
							continue
						prize_item_id = uuid_int(yield_stack.get("itemID"))
						prize_qty = int(yield_stack.get("qty"))
						success_rate = int(yield_stack.get("successRate"))
						ArcadePrize.objects.create(module_item_id=id, item_id=prize_item_id, qty=prize_qty, success_rate=success_rate)
				guest_cost = yield_elem.find("guestCost")
				if guest_cost is not None:
					for cost in guest_cost:
						cost_item_id = uuid_int(cost.get("itemID"))
						cost_qty = int(cost.get("qty"))
						ModuleExecutionCost.objects.create(module_item_id=id, item_id=cost_item_id, qty=cost_qty)
				owner_launch_cost = yield_elem.find("ownerLaunchCost")
				if owner_launch_cost is not None:
					for cost in owner_launch_cost:
						cost_item_id = uuid_int(cost.get("itemID"))
						cost_qty = int(cost.get("qty"))
						ModuleSetupCost.objects.create(module_item_id=id, item_id=cost_item_id, qty=cost_qty)

	for body in xml.findall("messages/category/body"):
		id = uuid_int(body.get("id"))
		subject = body.get("subject")
		text = body.get("text")
		MessageBody.objects.create(id=id, subject=subject, text=text)

	for body_elem in xml.findall("messages/category/body"):
		id = uuid_int(body_elem.get("id"))
		body = MessageBody.objects.get(id=id)
		for easy_reply in body_elem.findall("easyReplies/easyReply"):
			id = uuid_int(easy_reply.get("id"))
			easy_reply = MessageBody.objects.get(id=id)
			body.easy_replies.add(easy_reply)

	for question_elem in xml.findall("questions/question"):
		id = uuid_int(question_elem.get("id"))
		mandatory = question_elem.get("mandatory") == "True"
		question = Question.objects.create(id=id, text=question_elem.get("text"), mandatory=mandatory)
		for answer_elem in question_elem.findall("answer"):
			id = uuid_int(answer_elem.get("id"))
			Answer.objects.create(id=id, question=question, text=answer_elem.get("text"))

	for color in xml.findall("colors/color"):
		id = uuid.UUID(color.get("id")).node & 0xff # these UUIDs aren't actually proper UUIDs
		color_id = int(color.find("details").get("color"), 16)
		Color.objects.create(id=id, color=color_id)

	for skin in xml.findall("skins/skin"):
		id = uuid.UUID(skin.get("id")).node & 0xff # these UUIDs aren't actually proper UUIDs
		name = skin.get("name")
		ModuleSkin.objects.create(id=id, name=name)

def undo(apps, schema_editor):
	ItemInfo.objects.all().delete()
	MessageBody.objects.all().delete()
	Question.objects.all().delete()
	Answer.objects.all().delete()
	Color.objects.all().delete()
	ModuleSkin.objects.all().delete()

class Migration(migrations.Migration):
	dependencies = [
		("mln", "0001_initial"),
	]

	operations = [
		migrations.RunPython(import_xml, undo),
	]
