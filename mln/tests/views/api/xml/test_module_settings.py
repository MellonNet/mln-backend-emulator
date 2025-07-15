import os.path
import xml.etree.ElementTree as et

from django.template import loader

import mln.views.api.xml.module_settings as module_settings
from mln.models.static import ItemInfo, ItemType
from mln.models.dynamic.module_settings import ModuleSaveGeneric, ModuleSaveNetworkerText, ModuleSaveRocketGame, ModuleSaveSoundtrack, ModuleSaveSticker, ModuleSaveUGC, ModuleSetupFriendShare, ModuleSetupGroupPerformance, ModuleSetupTrade, ModuleSetupTrioPerformance
from mln.models.dynamic.module_settings_arcade import ModuleSaveConcertArcade, ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade
from mln.services.inventory import add_inv_item
from mln.tests.models.test_profile import one_user
from mln.tests.models.test_module import has_trade_module
from mln.tests.services.test_friend import friends, two_friends, three_friends
from mln.tests.services.test_misc import module
from mln.tests.setup_testcase import cls_setup, requires, setup, TestCase
from mln.tests.views.api.xml.test_module import background_item
from mln.templatetags.mln_utils import SAVE_TEMPLATES, SETUP_TEMPLATES

def _test_settings(self, cls):
	if cls in SAVE_TEMPLATES:
		name = SAVE_TEMPLATES[cls]
	elif cls in SETUP_TEMPLATES:
		name = SETUP_TEMPLATES[cls]
	path = os.path.normpath(os.path.join(__file__, "..", "res", "module", "settings", name+".xml"))
	settings = et.parse(path)
	module_settings._deserialize_cls(cls, self.module, settings, settings)
	resp = loader.get_template("mln/api/xml/module/settings/%s.xml" % name).render({"module": self.module})
	resp = "<settings>"+resp+"</settings>"

	with open(path) as file:
		expected = file.read()
	self.assertEqual(resp, expected)

#"concert_arcade", "generic", "hop_arcade", "soundtrack", "sticker", "ugc", "friend_share", "group_performance", "trade", "trio_performance"

def settings_meta(name, bases, attrs):
	for settings_cls in attrs["CLASSES"]:
		attrs["test_%s" % settings_cls.__name__] = (lambda cls: lambda self: _test_settings(self, cls))(settings_cls)
	return type(name, bases, attrs)

@setup
@requires(module, one_user)
def has_module(self):
	self.module = self.user.modules.create(item_id=self.MODULE_ITEM_ID, pos_x=0, pos_y=0)

@cls_setup
def loop(cls):
	cls.LOOP_ID = ItemInfo.objects.create(name="Loop", type=ItemType.LOOP).id

@setup
@requires(loop)
def has_loop(self):
	add_inv_item(self.user, self.LOOP_ID)

@cls_setup
def sticker_item(cls):
	cls.STICKER_ID = ItemInfo.objects.create(name="Sticker", type=ItemType.STICKER).id

@setup
@requires(sticker_item, background_item)
def has_stickers(self):
	add_inv_item(self.user, self.STICKER_ID)
	add_inv_item(self.user, self.BACKGROUND_ID)

@setup
@requires(has_trade_module)
def has_trade_module(self):
	self.module = self.t_module

class Settings(TestCase, metaclass=settings_meta):
	SETUP = has_module,
	CLASSES = ModuleSaveDeliveryArcade, ModuleSaveDestructoidArcade, ModuleSaveHopArcade, ModuleSaveNetworkerText, ModuleSaveRocketGame

class FriendShareSettings(TestCase, metaclass=settings_meta):
	SETUP = has_module, friends
	CLASSES = ModuleSetupFriendShare,

class GroupPerformanceSettings(TestCase, metaclass=settings_meta):
	SETUP = has_module, three_friends
	CLASSES = ModuleSetupGroupPerformance,

class SoundtrackSettings(TestCase, metaclass=settings_meta):
	SETUP = has_module, has_loop
	CLASSES = ModuleSaveSoundtrack, ModuleSaveConcertArcade

class StickerSettings(TestCase, metaclass=settings_meta):
	SETUP = has_module, has_stickers,
	CLASSES = ModuleSaveSticker,

class TradeSettings(TestCase, metaclass=settings_meta):
	SETUP = has_trade_module,
	CLASSES = ModuleSetupTrade,

class TrioPerformanceSettings(TestCase, metaclass=settings_meta):
	SETUP = has_module, two_friends
	CLASSES = ModuleSetupTrioPerformance,

class UGCSettings(TestCase, metaclass=settings_meta):
	SETUP = has_module,
	CLASSES = ModuleSaveUGC,
