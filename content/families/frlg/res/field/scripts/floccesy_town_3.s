#include "asm/field_script.inc"
#include "text/script/floccesy_town_3.h"
#include "frlg_story.inc"

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntry Script_4
    ScriptEntriesEnd

// The clerk: Oak's Parcel is waiting until it's delivered; then the Mart sells, through Black 2's own Mart
Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_HAS_POKEDEX, Clerk_Errand
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, B2_MART_STANDARD
    WorkSetConst 0x8001, 1
    RTCallGlobal B2_SCRIPT_MART
    VMStackPop 0x8001
    VMStackPop 0x8000
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Clerk_Errand:
    ParentActorMsg MSGFILE_SCRIPT, ViridianMart_Text_Npc1_2, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_2:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianMart_Text_Npc2_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_3:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianMart_Text_Npc3_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// On first coming in after the rival's battle: the clerk calls out and gives the player Oak's Parcel (Black 2's Parcel)
Script_4:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorMsg MSGFILE_SCRIPT, ViridianMart_Text_MapScript1_0, 1, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, ViridianMart_Text_MapScript1_1, 1, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ItemAdd ITEM_PARCEL, 1, 0x8010
    WordSetPlayerName 0
    MEPlay SEQ_ME_KEYITEM
    SystemMsg ViridianMart_Text_MapScript1_2, 1
    MEWait
    MsgWaitAdvance
    SystemMsgClose
    WorkSetConst KANTO_VAR_STORY, KANTO_STORY_HAS_PARCEL
    ActorsUnpauseAll
    VMHalt
    .balign 4, 0
