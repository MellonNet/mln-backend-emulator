"""Handlers for module specific save data updates."""
from ....models.dynamic.module_settings import ModuleSaveGeneric, ModuleSaveNetworkerPic, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupGroupPerformance, ModuleSetupTrade, ModuleSetupTrioPerformance, RocketGameTheme
from ....models.dynamic.module_settings_arcade import DestructoidBlockSkin, DestructoidCharacterSkin, HopArcadeElement, ModuleSaveConcertArcade, ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade
from ....services.module_settings import create_or_update, get_or_create_module

def _deserialize_concert_arcade(save, setup):
	attrs = {}
	game_setting = save.find("gameSetting")
	attrs["owner_played"] = game_setting.get("ownerPlayed") == "true"
	bg, arrowset = game_setting.get("skins").split(",")
	attrs["background_skin"] = int(bg[bg.rindex("_")+1:])
	attrs["arrowset_skin"] = int(arrowset[arrowset.rindex("_")+1:])
	for arrows_name, line in zip(("arrows_left", "arrows_down", "arrows_up", "arrows_right"), game_setting.findall("concertLines")):
		arrows = 0
		i = 0
		for arrow in line.findall("arrow"):
			bit = arrow.get("type") != "noArrow"
			if bit:
				arrows |= 1 << i
			i += 1
		arrows = int.from_bytes(arrows.to_bytes(8, "big"), "big", signed=True) # unsigned signed conversion
		attrs[arrows_name] = arrows
	return attrs

def _deserialize_delivery_arcade(module, save, setup):
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
	return attrs

def _deserialize_destructoid_arcade(save, setup):
	game_setting = save.find("gameSetting")
	attrs = {}
	attrs["owner_played"] = game_setting.get("ownerPlayed") == "true"
	if game_setting.get("energyUsed") == "undefined":
		attrs["energy_used"] = 0
	else:
		attrs["energy_used"] = int(game_setting.get("energyUsed"))
	character, block, background = game_setting.get("skins").split(",")
	attrs["character_skin"] = DestructoidCharacterSkin[character[2:].upper()]
	attrs["block_skin"] = DestructoidBlockSkin[block[2:].upper()]
	attrs["background_skin"] = int(background[5:])
	rows = [0, 0, 0]
	for i, column in enumerate(game_setting.findall("column")):
		for j, row in enumerate(column.findall("row")):
			density = int(row.get("density"))
			rows[j] |= density << i*3

	attrs["top"] = rows[0]
	attrs["middle"] = rows[1]
	attrs["bottom"] = rows[2]
	return attrs

def _deserialize_friend_share(save, setup):
	friend_id = int(setup.find("friend").get("friendID"))
	attrs = {}
	attrs["friend_id"] = friend_id
	return attrs

def _deserialize_generic(save, setup):
	attrs = {}
	skin_id = save.get("skin")
	if skin_id is not None:
		skin_id = int(skin_id)
		attrs["skin_id"] = skin_id
	color_id = save.get("color")
	if color_id is not None:
		color_id = int(color_id)
		attrs["color_id"] = color_id
	return attrs

def _deserialize_group_performance(save, setup):
	friends = setup.findall("friend")
	friend_0_id = int(friends[0].get("friendID"))
	friend_1_id = int(friends[1].get("friendID"))
	friend_2_id = int(friends[2].get("friendID"))
	attrs = {}
	attrs["friend_0_id"] = friend_0_id
	attrs["friend_1_id"] = friend_1_id
	attrs["friend_2_id"] = friend_2_id
	return attrs

def _deserialize_hop_arcade(save, setup):
	game_setting = save.find("gameSetting")
	attrs = {}
	attrs["owner_played"] = game_setting.get("ownerPlayed") == "true"
	rows = [0, 0, 0]
	for i, column in enumerate(game_setting.findall("column")):
		for j, row in enumerate(column.findall("row")):
			frame = row.get("frame")
			if frame == "0":
				continue
			val = HopArcadeElement[frame[2:].upper()].value
			rows[j] |= val << i*3

	for i, name in enumerate(("top", "middle", "bottom")):
		for j in range(3):
			attrs["%s_%i" % (name, j)] = (rows[i] >> (j * 30)) & 0x3fffffff
	return attrs

def _deserialize_networker_pic(module, save, setup):
	# the flash sticker editor is broken for networker pics anyway
	pass

def _deserialize_networker_text(save, setup):
	attrs = {}
	attrs["text"] = save.find("text").text
	return attrs

def _deserialize_rocket_game(save, setup):
	attrs = {}
	attrs["theme"] = RocketGameTheme[save.find("theme").text.upper()]
	return attrs

def _deserialize_soundtrack(save, setup):
	attrs = {}
	for i, track in enumerate(save.findall("track")):
		for j, sound in enumerate(track):
			id = sound.get("id")
			if id == "blankSound":
				id = None
			else:
				id = int(id)
			pan = int(sound.get("pan"))
			attrs["sound_%i_%i_id" % (i, j)] = id
			attrs["sound_%i_%i_pan" % (i, j)] = pan
	return attrs

def _deserialize_sticker(module, save, setup):
	# easiest way of doing things
	module.save_sticker.all().delete()
	for movieclip in save.findall("Movieclip"):
		attrs = {}
		attrs["item_id"] = int(movieclip.get("id"))
		attrs["x"] = float(movieclip.get("_x"))
		attrs["y"] = float(movieclip.get("_y"))
		attrs["scale_x"] = int(movieclip.get("_xscale"))
		attrs["scale_y"] = int(movieclip.get("_yscale"))
		attrs["rotation"] = int(movieclip.get("_rotation"))
		attrs["depth"] = int(movieclip.get("depth"))
		module.save_sticker.create(**attrs)

def _deserialize_trade(save, setup):
	attrs = {}
	give = setup.find("item[@type='Give']")
	request = setup.find("item[@type='Request']")
	attrs["give_item_id"] = int(give.get("itemID"))
	attrs["give_qty"] = int(give.get("qty"))
	attrs["request_item_id"] = int(request.get("itemID"))
	attrs["request_qty"] = int(request.get("qty"))
	return attrs

def _deserialize_trio_performance(save, setup):
	friends = setup.findall("friend")
	friend_0_id = int(friends[0].get("friendID"))
	friend_1_id = int(friends[1].get("friendID"))
	attrs = {}
	attrs["friend_0_id"] = friend_0_id
	attrs["friend_1_id"] = friend_1_id
	return attrs

def _deserialize_ugc(save, setup):
	attrs = {}
	attrs["ref"] = int(save.find("Movieclip").get("id"))
	return attrs

SETTINGS_HANDLERS = {
	ModuleSaveConcertArcade: _deserialize_concert_arcade,
	ModuleSaveDestructoidArcade: _deserialize_destructoid_arcade,
	ModuleSaveGeneric: _deserialize_generic,
	ModuleSaveHopArcade: _deserialize_hop_arcade,
	ModuleSaveNetworkerPic: _deserialize_networker_pic,
	ModuleSaveNetworkerText: _deserialize_networker_text,
	ModuleSaveRocketGame: _deserialize_rocket_game,
	ModuleSaveSoundtrack: _deserialize_soundtrack,
	ModuleSaveUGC: _deserialize_ugc,
	ModuleSetupFriendShare: _deserialize_friend_share,
	ModuleSetupGroupPerformance: _deserialize_group_performance,
	ModuleSetupTrade: _deserialize_trade,
	ModuleSetupTrioPerformance: _deserialize_trio_performance,
}

def _deserialize_cls(cls, module, save, setup):
	# unfortunately the settings system is not very cleanly made and there are some anomalies
	if cls == ModuleSetupTrade:
		if module.is_setup:
			module.teardown()
	if cls == ModuleSaveSticker:
		_deserialize_sticker(module, save, setup)
	elif cls == ModuleSaveDeliveryArcade:
		attrs = _deserialize_delivery_arcade(module, save, setup)
		create_or_update(cls, module, attrs)
	else:
		attrs = SETTINGS_HANDLERS[cls](save, setup)
		create_or_update(cls, module, attrs)
		if cls == ModuleSaveConcertArcade:
			game_setting = save.find("gameSetting")
			attrs = _deserialize_soundtrack(game_setting, setup)
			create_or_update(ModuleSaveSoundtrack, module, attrs)

def handle_module_save_settings(user, request):
	instance_id = request.get("instanceID")
	if instance_id == "00000000-0000-0000-0000-000000000000":
		instance_id = None
	else:
		instance_id = int(instance_id)
	item_id = int(request.get("itemID"))
	module = get_or_create_module(user, instance_id, item_id)
	save = request.find("result/save")
	setup = request.find("result/setup")
	for cls in module.get_settings_classes():
		_deserialize_cls(cls, module, save, setup)
	return {"module": module}
