"""Handlers for module specific save data updates."""
import uuid

from ..models.module_settings import ModuleSaveGeneric, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupGroupPerformance, ModuleSetupTrade, ModuleSetupTrioPerformance, RocketGameTheme
from ..models.module_settings_arcade import DestructoidBlockSkin, DestructoidCharacterSkin, ModuleSaveConcertArcade, ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade
from ..models.static import ModuleInfo
from .page import get_or_create_module
from .utils import uuid_int

def create_or_update(cls, module, attrs):
	save_obj, created = cls.objects.get_or_create(module=module, defaults=attrs)
	if not created:
		for key, value in attrs.items():
			setattr(save_obj, key, value)
		save_obj.save()

def deserialize_concert_arcade(module, save, setup):
	game_setting = save.find("gameSetting")
	deserialize_soundtrack(module, game_setting, setup)
	attrs = {}
	attrs["owner_played"] = game_setting.get("ownerPlayed") == "true"
	bg, arrowset = game_setting.get("skins").split(",")
	attrs["background_skin"] = int(bg[bg.rindex("_")+1:])
	attrs["arrowset_skin"] = int(arrowset[arrowset.rindex("_")+1:])
	arrows = 0
	i = 0
	for lines in game_setting.findall("concertLines"):
		for arrow in lines.findall("arrow")[3::4]:
			bit = arrow.get("type") != "noArrow"
			if bit:
				arrows |= 1 << i
			i += 1
	attrs["arrows"] = arrows
	create_or_update(ModuleSaveConcertArcade, module, attrs)

def deserialize_delivery_arcade(module, save, setup):
	game_setting = save.find("gameSetting")
	attrs = {}
	attrs["owner_played"] = game_setting.get("ownerPlayed") == "true"
	if game_setting.get("timer") == "NaN":
		attrs["timer"] = 0
	else:
		attrs["timer"] = int(game_setting.get("timer"))
	for checkpoint in game_setting.findall("cp"):
		cp = checkpoint.get("t")[2:]
		attrs["%s_x" % cp] = int(checkpoint.get("x"))
		attrs["%s_y" % cp] = int(checkpoint.get("y"))
	module.tiles.all().delete()
	for tile in game_setting.findall("tile"):
		t_type, t_id = tile.get("t").rsplit("_", 1)
		t_id = int(t_id)
		if t_type == "m_scen":
			t_id |= (1 << 5)
		x = int(tile.get("x"))
		y = int(tile.get("y"))
		module.tiles.create(tile_id=t_id, x=x, y=y)
	create_or_update(ModuleSaveDeliveryArcade, module, attrs)

def deserialize_destructoid_arcade(module, save, setup):
	game_setting = save.find("gameSetting")
	attrs = {}
	attrs["owner_played"] = game_setting.get("ownerPlayed") == "true"
	if game_setting.get("energyUsed") == "undefined":
		attrs["energy_used"] = 0
	else:
		attrs["energy_used"] = int(game_setting.get("energyUsed"))
	character, block, background = game_setting.get("skins").split(",")
	attrs["character_skin"] = DestructoidCharacterSkin[character[2:].upper()].value
	attrs["block_skin"] = DestructoidBlockSkin[block[2:].upper()].value
	attrs["background_skin"] = int(background[5:])
	rows = [0, 0, 0]
	for i, column in enumerate(game_setting.findall("column")):
		for j, row in enumerate(column.findall("row")):
			density = int(row.get("density"))
			rows[j] |= density << i*3

	attrs["top"] = rows[0]
	attrs["middle"] = rows[1]
	attrs["bottom"] = rows[2]

	create_or_update(ModuleSaveDestructoidArcade, module, attrs)

def deserialize_friend_share(module, save, setup):
	friend_id = int(setup.find("friend").get("friendID"))
	attrs = {}
	attrs["friend_id"] = friend_id

	create_or_update(ModuleSetupFriendShare, module, attrs)

def deserialize_generic(module, save, setup):
	attrs = {}
	skin_id = save.get("skin")
	if skin_id is not None:
		skin_id = uuid.UUID(skin_id).node & 0xff # these UUIDs aren't actually proper UUIDs
		attrs["skin_id"] = skin_id
	color_id = save.get("color")
	if color_id is not None:
		color_id = uuid.UUID(color_id).node & 0xff # these UUIDs aren't actually proper UUIDs
		attrs["color_id"] = color_id

	create_or_update(ModuleSaveGeneric, module, attrs)

def deserialize_group_performance(module, save, setup):
	friends = setup.findall("friend")
	friend_0_id = int(friends[0].get("friendID"))
	friend_1_id = int(friends[1].get("friendID"))
	friend_2_id = int(friends[2].get("friendID"))
	attrs = {}
	attrs["friend_0_id"] = friend_0_id
	attrs["friend_1_id"] = friend_1_id
	attrs["friend_2_id"] = friend_2_id

	create_or_update(ModuleSetupGroupPerformance, module, attrs)

def deserialize_hop_arcade(module, save, setup):
	game_setting = save.find("gameSetting")
	attrs = {}
	attrs["owner_played"] = game_setting.get("ownerPlayed") == "true"
	rows = [0, 0, 0]
	for i, column in enumerate(game_setting.findall("column")):
		for j, row in enumerate(column.findall("row")):
			frame = row.get("frame")
			if frame == "0":
				continue
			val = ModuleSaveHopArcade.HOP_ELEMENT_ENUMS[j][frame[2:].upper()].value
			rows[j] |= val << i*2

	attrs["top"] = rows[0]
	attrs["middle"] = rows[1]
	attrs["bottom"] = rows[2]

	create_or_update(ModuleSaveHopArcade, module, attrs)

def deserialize_networker_text(module, save, setup):
	attrs = {}
	attrs["text"] = save.find("text").text

	create_or_update(ModuleSaveNetworkerText, module, attrs)

def deserialize_rocket_game(module, save, setup):
	attrs = {}
	attrs["theme"] = RocketGameTheme[save.find("theme").text.upper()].value

	create_or_update(ModuleSaveRocketGame, module, attrs)

def deserialize_soundtrack(module, save, setup):
	attrs = {}
	for i, track in enumerate(save.findall("track")):
		for j, sound in enumerate(track):
			id = sound.get("id")
			if id == "blankSound":
				id = None
			else:
				id = uuid_int(id)
			pan = int(sound.get("pan"))
			attrs["sound_%i_%i_id" % (i, j)] = id
			attrs["sound_%i_%i_pan" % (i, j)] = pan

	create_or_update(ModuleSaveSoundtrack, module, attrs)

def deserialize_sticker(module, save, setup):
	# easiest way of doing things
	module.save_sticker.all().delete()
	for movieclip in save.findall("Movieclip"):
		attrs = {}
		attrs["item_id"] = uuid_int(movieclip.get("id"))
		attrs["x"] = float(movieclip.get("_x"))
		attrs["y"] = float(movieclip.get("_y"))
		attrs["scale_x"] = int(movieclip.get("_xscale"))
		attrs["scale_y"] = int(movieclip.get("_yscale"))
		attrs["rotation"] = int(movieclip.get("_rotation"))
		attrs["depth"] = int(movieclip.get("depth"))

		module.save_sticker.create(module=module, **attrs)

def deserialize_trade(module, save, setup):
	if module.is_setup:
		module.teardown()
	attrs = {}
	give = setup.find("item[@type='Give']")
	request = setup.find("item[@type='Request']")
	attrs["give_item_id"] = uuid_int(give.get("itemID"))
	attrs["give_qty"] = int(give.get("qty"))
	attrs["request_item_id"] = uuid_int(request.get("itemID"))
	attrs["request_qty"] = int(request.get("qty"))

	create_or_update(ModuleSetupTrade, module, attrs)

def deserialize_trio_performance(module, save, setup):
	friends = setup.findall("friend")
	friend_0_id = int(friends[0].get("friendID"))
	friend_1_id = int(friends[1].get("friendID"))
	attrs = {}
	attrs["friend_0_id"] = friend_0_id
	attrs["friend_1_id"] = friend_1_id

	create_or_update(ModuleSetupTrioPerformance, module, attrs)

def deserialize_ugc(module, save, setup):
	attrs = {}
	attrs["ref"] = int(save.find("Movieclip").get("id"))

	create_or_update(ModuleSaveUGC, module, attrs)

SETTINGS_HANDLERS = {
	ModuleSaveConcertArcade: deserialize_concert_arcade,
	ModuleSaveDestructoidArcade: deserialize_destructoid_arcade,
	ModuleSaveDeliveryArcade: deserialize_delivery_arcade,
	ModuleSaveGeneric: deserialize_generic,
	ModuleSaveHopArcade: deserialize_hop_arcade,
	ModuleSaveNetworkerText: deserialize_networker_text,
	ModuleSaveRocketGame: deserialize_rocket_game,
	ModuleSaveSoundtrack: deserialize_soundtrack,
	ModuleSaveSticker: deserialize_sticker,
	ModuleSaveUGC: deserialize_ugc,
	ModuleSetupFriendShare: deserialize_friend_share,
	ModuleSetupGroupPerformance: deserialize_group_performance,
	ModuleSetupTrade: deserialize_trade,
	ModuleSetupTrioPerformance: deserialize_trio_performance,
}

def handle_module_save_settings(user, request):
	module = get_or_create_module(user, request)
	for cls in module.get_settings_classes():
		SETTINGS_HANDLERS[cls](module, request.find("result/save"), request.find("result/setup"))

	info = ModuleInfo.objects.get(item_id=module.item_id)
	if info.is_executable and not info.is_setupable:
		module.is_setup = True
		module.save()

	return {"module": module}
