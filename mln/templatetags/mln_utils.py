"""Various utility functions for accessing or formatting data for templates that would be too complex to do in the templates themselves."""
import re
from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.template.base import DebugLexer, Lexer, tag_re, TextNode

from mln.models.dynamic.module_settings import ModuleSaveGeneric, ModuleSaveNetworkerPic, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupGroupPerformance, ModuleSetupTrade, ModuleSetupTrioPerformance
from mln.models.dynamic.module_settings_arcade import HopArcadeElement, ModuleSaveConcertArcade, ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade
from mln.models.dynamic import get_or_none as get_model
from mln.models.static import ItemType, MessageReplyType, ItemInfo

SAVE_TEMPLATES = {
	ModuleSaveConcertArcade: "concert_arcade",
	ModuleSaveDeliveryArcade: "delivery_arcade",
	ModuleSaveDestructoidArcade: "destructoid_arcade",
	ModuleSaveHopArcade: "hop_arcade",
	ModuleSaveNetworkerPic: "networker_pic",
	ModuleSaveNetworkerText: "networker_text",
	ModuleSaveSoundtrack: "soundtrack",
	ModuleSaveSticker: "sticker",
	ModuleSaveRocketGame: "rocket_game",
	ModuleSaveUGC: "ugc",
}
SETUP_TEMPLATES = {
	ModuleSetupFriendShare: "friend_share",
	ModuleSetupGroupPerformance: "group_performance",
	ModuleSetupTrade: "trade",
	ModuleSetupTrioPerformance: "trio_performance",
}

register = template.Library()

@register.filter
def get_avatar(profile):
	"""
	Get the avatar including whether the user is a networker, which is for some reason part of the avatar field.
	Also, in case of png avatars, return the actual path.
	"""
	avatar = profile.avatar
	if avatar == "png":
		avatar = "url#[npfp]"+profile.user.username+".png"
	if profile.is_networker:
		avatar += "#n"
	return avatar

@register.filter
def get_concert_arcade_arrows(module):

	for arrows_name, arrows_type in (("arrows_left", "-90"), ("arrows_down", "180"), ("arrows_up", "0"), ("arrows_right", "90")):
		arrows = getattr(module.save_concert_arcade, arrows_name)
		line = []
		for _ in range(64):
			if arrows & 1:
				line.append(arrows_type)
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
	char = module.save_destructoid_arcade.character_skin.name.lower()
	block = module.save_destructoid_arcade.block_skin.name.lower()
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
	save = module.save_hop_arcade
	rows = "top", "middle", "bottom"
	for i in range(30):
		column = []
		for j in range(3):
			value = getattr(save, "%s_%i" % (rows[j], i // 10))
			elem_value = value & 0x07
			if elem_value == 0:
				column.append("0")
			else:
				column.append("m_"+HopArcadeElement(elem_value).name.lower())
			setattr(save, "%s_%i" % (rows[j], i // 10), value >> 3)
		yield column

@register.filter
def get_generic_settings(module):
	if ModuleSaveGeneric not in module.get_settings_classes():
		return None
	return getattr(module, "save_generic", None)

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
			yield "mln/api/xml/module/settings/"+SAVE_TEMPLATES[cls]+".xml"

@register.filter
def get_setup_templates(module):
	for cls in module.get_settings_classes():
		if cls in SETUP_TEMPLATES:
			yield "mln/api/xml/module/settings/"+SETUP_TEMPLATES[cls]+".xml"

@register.filter
def is_background(sticker):
	return sticker.item.type == ItemType.BACKGROUND

@register.filter
def replyable(message):
	if message.body.easy_replies.exists():
		return MessageReplyType.NORMAL_AND_EASY_REPLY.value
	else:
		return MessageReplyType.NORMAL_REPLY_ONLY.value

@register.filter
def get_valid_modules(owner):
	return owner.modules.filter(pos_x__isnull=False, pos_y__isnull=False)

@register.filter
def get_trophies(owner):
	result = []
	for trophyID in ["103022", "103030", "103026", "103024", "103021", "103032", "103031"]:
		try:
			trophy = owner.inventory.get(item__id=trophyID)
			result.append(trophy.item)
		except ObjectDoesNotExist:
			continue
	return result

# Fix for Django template compilation, to remove whitespace from templates.
# The two tokenize functions are changed to avoid generating a TextNode when the text content is only whitespace.
# The TextNode constructor is changed to remove as much whitespace as possible from the content.

def tokenize_fix(self):
	in_tag = False
	lineno = 1
	result = []
	for bit in tag_re.split(self.template_string):
		if bit.strip():
			result.append(self.create_token(bit, None, lineno, in_tag))
		in_tag = not in_tag
		lineno += bit.count('\n')
	return result

Lexer.tokenize = tokenize_fix

def debug_tokenize_fix(self):
	lineno = 1
	result = []
	upto = 0
	for match in tag_re.finditer(self.template_string):
		start, end = match.span()
		if start > upto:
			token_string = self.template_string[upto:start]
			if token_string.strip():
				result.append(self.create_token(token_string, (upto, start), lineno, in_tag=False))
			lineno += token_string.count('\n')
			upto = start
		token_string = self.template_string[start:end]
		if token_string.strip():
			result.append(self.create_token(token_string, (start, end), lineno, in_tag=True))
		lineno += token_string.count('\n')
		upto = end
	last_bit = self.template_string[upto:]
	if last_bit.strip():
		result.append(self.create_token(last_bit, (upto, upto + len(last_bit)), lineno, in_tag=False))
	return result

def whitespace_fix(self, s):
	"""
	Remove whitespace surrounding XML tags (same as standard django tag "spaceless") and also remove whitespace surrounding django template language constructs.
	The result should be XML as much whitespace removed as possible.
	Also, since this is done at template compilation time and not at template rendering time (which is where "spaceless" executes for some reason), it's also faster than "spaceless".
	"""
	s = re.sub(r"(^\s+)|(\s+$)", " ", s) # if the string starts or ends with whitespace replace it with a single space (needed for some edge cases)
	# remove whitespace near tag boundaries
	s = re.sub(r"\s*(/?>)\s*", r"\1", s)
	s = re.sub(r"\s+<", "<", s)
	self.s = s

def render_to_string_stripped(template, context):
	olt = Lexer.tokenize
	odlt = DebugLexer.tokenize
	Lexer.tokenize = tokenize_fix
	DebugLexer.tokenize = debug_tokenize_fix
	res = loader.render_to_string(template, context)
	Lexer.tokenize = olt
	DebugLexer.tokenize = odlt
	return res


TextNode.__init__ = whitespace_fix
