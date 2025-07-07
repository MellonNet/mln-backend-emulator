from .info import *
from .settings import *
from .settings_arcade import *

"""Settings class registry. This links module editor types to settings classes."""
module_settings_classes = {
	ModuleEditorType.CONCERT_I_ARCADE: (ModuleSaveConcertArcade,),
	ModuleEditorType.CONCERT_II_ARCADE: (ModuleSaveConcertArcade,),
	ModuleEditorType.DELIVERY_ARCADE: (ModuleSaveDeliveryArcade,),
	ModuleEditorType.DESTRUCTOID_ARCADE: (ModuleSaveDestructoidArcade,),
	ModuleEditorType.DR_INFERNO_ROBOT_SIM: (ModuleSaveDestructoidArcade,),
	ModuleEditorType.FACTORY_GENERIC: (ModuleSaveGeneric, ModuleSaveUGC),
	ModuleEditorType.FACTORY_NON_GENERIC: (ModuleSaveUGC,),
	ModuleEditorType.FRIEND_SHARE: (ModuleSaveGeneric, ModuleSetupFriendShare),
	ModuleEditorType.FRIENDLY_FELIX_CONCERT: (ModuleSaveConcertArcade,),
	ModuleEditorType.GALLERY_GENERIC: (ModuleSaveGeneric, ModuleSaveUGC),
	ModuleEditorType.GALLERY_NON_GENERIC: (ModuleSaveUGC,),
	ModuleEditorType.GENERIC: (ModuleSaveGeneric,),
	ModuleEditorType.GROUP_PERFORMANCE: (ModuleSaveGeneric, ModuleSetupGroupPerformance),
	ModuleEditorType.HOP_ARCADE: (ModuleSaveHopArcade,),
	ModuleEditorType.LOOP_SHOPPE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.NETWORKER_PIC: (ModuleSaveNetworkerPic,),
	ModuleEditorType.NETWORKER_TEXT: (ModuleSaveGeneric, ModuleSaveNetworkerText),
	ModuleEditorType.NETWORKER_TRADE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.PLASTIC_PELLET_INDUCTOR: (ModuleSaveUGC,),
	ModuleEditorType.ROCKET_GAME: (ModuleSaveSticker, ModuleSaveRocketGame),
	ModuleEditorType.SOUNDTRACK: (ModuleSaveGeneric, ModuleSaveSoundtrack),
	ModuleEditorType.STICKER: (ModuleSaveSticker,),
	ModuleEditorType.STICKER_SHOPPE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.TRADE: (ModuleSaveGeneric, ModuleSetupTrade),
	ModuleEditorType.TRIO_PERFORMANCE: (ModuleSaveGeneric, ModuleSetupTrioPerformance),
	None: (),
}
