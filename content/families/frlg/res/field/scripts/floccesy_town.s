#include "asm/field_script.inc"
#include "text/script/floccesy_town.h"
#include "frlg_story.inc"

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntry Script_4
    ScriptEntry Script_5
    ScriptEntry Script_6
    ScriptEntry Script_7
    ScriptEntry Script_8
    ScriptEntry Script_9
    ScriptEntriesEnd

Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc1_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_2:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc3_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// The old man: he forbids the way north until the parcel is delivered, then has had his coffee
Script_3:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_HAS_POKEDEX, OldMan_Forbids
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc4_0, 0, 0
    VMJump OldMan_Talked

OldMan_Forbids:
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc4_4, 0, 0

OldMan_Talked:
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// His granddaughter: apologizing for him until the parcel is delivered
Script_4:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_HAS_POKEDEX, Granddaughter_Sorry
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc5_0, 0, 0
    VMJump Granddaughter_Talked

Granddaughter_Sorry:
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc5_1, 0, 0

Granddaughter_Talked:
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_5:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc6_1, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_6:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc7_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_7:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign ViridianCity_Text_Sign1_0, 2
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_8:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign ViridianCity_Text_Sign3_0, 1
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// The way north, until the parcel is delivered: the old man forbids it and the player steps back, at the row where
// Black 2's own story blocks the same way
Script_9:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc4_4, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    PlayerGetGPos 0x8021, 0x8022
    ActorWalkRoute 255, 0x8021, 671, 0, 8, 0
    ActorCmdWait
    ActorsUnpauseAll
    VMHalt
    .balign 4, 0
