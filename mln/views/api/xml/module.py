from ....models.module import Module
from ....models.static import ItemInfo, ItemType

def handle_get_module_bgs(user, request):
	item_id = int(request.get("id")) # todo: do something with this
	backgrounds = [info.id for info in ItemInfo.objects.filter(type=ItemType.BACKGROUND)]
	return {"backgrounds": backgrounds}

def module_handler(func):
	def base_handler(user, request):
		instance_id = int(request.get("instanceID"))
		module = Module.objects.get(id=instance_id)
		return func(user, module)
	return base_handler

def handle_module_collect_winnings(user, request):
	instance_id = int(request.get("instanceID"))
	module = Module.objects.get(id=instance_id)
	won = request.get("won") == "True"
	# todo: arcade stats
	if won:
		prize = module.select_arcade_prize(user)
		return {"won": won, "prize": prize}
	else:
		return {"won": won}

@module_handler
def handle_module_details(user, module):
	return {"module": module}

@module_handler
def handle_module_execute(user, module):
	module.execute(user)
	return {"module": module, "available_votes": user.profile.available_votes}

@module_handler
def handle_module_harvest(user, module):
	module.harvest()

@module_handler
def handle_module_setup(user, module):
	module.setup()

@module_handler
def handle_module_teardown(user, module):
	module.teardown()

@module_handler
def handle_module_vote(voter, module):
	module.vote(voter)
	return {"available_votes": voter.profile.available_votes}
