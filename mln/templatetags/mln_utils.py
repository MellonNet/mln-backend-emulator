"""Various utility functions for accessing or formatting data for templates that would be too complex to do in the templates themselves."""
from django import template

from mln.models.module_settings import ModuleSaveGeneric, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupTrade
from mln.models.module_settings_arcade import DestructoidBlockSkin, DestructoidCharacterSkin, ModuleSaveConcertArcade, ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade
from mln.models.static import ItemType, MessageReplyType

SAVE_TEMPLATES = {
	ModuleSaveConcertArcade: "concert_arcade",
	ModuleSaveDeliveryArcade: "delivery_arcade",
	ModuleSaveDestructoidArcade: "destructoid_arcade",
	ModuleSaveHopArcade: "hop_arcade",
	ModuleSaveNetworkerText: "networker_text",
	ModuleSaveSoundtrack: "soundtrack",
	ModuleSaveSticker: "sticker",
	ModuleSaveRocketGame: "rocket_game",
	ModuleSaveUGC: "ugc",
}
SETUP_TEMPLATES = {
	ModuleSetupFriendShare: "friend_share",
	ModuleSetupTrade: "trade",
}

register = template.Library()

@register.filter
def get_avatar(profile):
	"""Get the avatar including whether the user is a networker, which is for some reason part of the avatar field."""
	if profile.is_networker:
		return profile.avatar+"#n"
	return profile.avatar

@register.filter
def get_concert_arcade_arrows(module):
	arrows = module.save_concert_arcade.arrows
	for arrowtype in "-90", "180", "0", "90":
		line = []
		for _ in range(16):
			if arrows & 1:
				line.append(arrowtype)
			else:
				line.append("noArrow")
			arrows >>= 1
		yield line

@register.filter
def get_delivery_checkpoints(save):
	for checkpoint in ("house_0", "house_1", "house_2", "start"):
		x = getattr(save, "%s_x" % checkpoint)
		if x is not None:
			yield "m_%s" % checkpoint, x, getattr(save, "%s_y" % checkpoint)

@register.filter
def get_delivery_tile_name(tile):
	if tile.tile_id & (1 << 5):
		return "m_scen_%i" % (tile.tile_id & ((1 << 5) - 1))
	else:
		return "m_tile_%i" % tile.tile_id

@register.filter
def get_destructoid_arcade_skins(module):
	char = DestructoidCharacterSkin(module.save_destructoid_arcade.character_skin).name.lower()
	block = DestructoidBlockSkin(module.save_destructoid_arcade.character_skin).name.lower()
	return "m_%s,m_%s,m_bg_%i" % (char, block, module.save_destructoid_arcade.background_skin)

@register.filter
def get_destructoid_arcade_grid(module):
	rows = [module.save_destructoid_arcade.top, module.save_destructoid_arcade.middle, module.save_destructoid_arcade.bottom]
	for i in range(11):
		column = []
		for j in range(3):
			value = rows[j] & 0x07
			column.append(value)
			rows[j] >>= 3
		yield column

@register.filter
def get_hop_arcade_grid(module):
	rows = [module.save_hop_arcade.top, module.save_hop_arcade.middle, module.save_hop_arcade.bottom]
	for i in range(30):
		column = []
		for j in range(3):
			value = rows[j] & 0x03
			if value == 0:
				column.append("0")
			else:
				column.append("m_"+ModuleSaveHopArcade.HOP_ELEMENT_ENUMS[j](value).name.lower())
			rows[j] >>= 2
		yield column

@register.filter
def get_generic_settings(module):
	if ModuleSaveGeneric not in module.get_settings_classes():
		return None
	return getattr(module, "save_generic", None)

@register.filter
def get_item_type_name(item_info):
	return ItemType(item_info.type).name.lower()

@register.filter
def get_or_none(obj, name):
	return getattr(obj, name, None)

@register.filter
def get_save_soundtrack(module):
	save = get_or_none(module, "save_soundtrack")
	if save is None:
		return []

	tracks = []
	for i in range(4):
		track = []
		for j in range(4):
			id = getattr(save, "sound_%i_%i_id" % (i, j))
			if id is None:
				id = "blankSound"
			else:
				id = str(id)
			pan = getattr(save, "sound_%i_%i_pan" % (i, j))
			track.append((id, pan))
		tracks.append(track)
	return tracks

@register.filter
def get_save_templates(module):
	for cls in module.get_settings_classes():
		if cls in SAVE_TEMPLATES:
			yield "mln/webservice/module/settings/"+SAVE_TEMPLATES[cls]+".xml"

@register.filter
def get_setup_templates(module):
	for cls in module.get_settings_classes():
		if cls in SETUP_TEMPLATES:
			yield "mln/webservice/module/settings/"+SETUP_TEMPLATES[cls]+".xml"

@register.filter
def is_background(sticker):
	return sticker.item.type == ItemType.BACKGROUND

@register.filter
def replyable(message):
	if message.body.easy_replies.exists():
		return MessageReplyType.NORMAL_AND_EASY_REPLY
	else:
		return MessageReplyType.NORMAL_REPLY_ONLY
