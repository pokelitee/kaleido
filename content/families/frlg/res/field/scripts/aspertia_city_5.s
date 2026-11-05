#include "asm/field_script.inc"
#include "text/script/aspertia_city_5.h"
#include "frlg_story.inc"

    ScriptEntry Script_1
    ScriptEntriesEnd

// Daisy: once the player has the Pokédex, she gives the Town Map, through Black 2's own item-receiving script, if the
// bag has room; until then, and after, her own lines
Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    WordSetPlayerName 0
    WordSetLoadRivalName 1
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_HAS_POKEDEX, Daisy_Before
    KantoUnlessFlag KANTO_FLAG_GOT_TOWN_MAP, Daisy_TownMap
    ParentActorMsg MSGFILE_SCRIPT, RivalsHouse_Text_Npc1_4, 0, 0
    VMJump Daisy_Talked

Daisy_TownMap:
    ParentActorMsg MSGFILE_SCRIPT, RivalsHouse_Text_Npc1_2, 0, 0
    LastKeyWait
    ActorMsgClose
    ItemCheckSpace ITEM_TOWN_MAP, 1, 0x8010
    KantoUnlessEqual 0x8010, 0, Daisy_Give
    ParentActorMsg MSGFILE_SCRIPT, RivalsHouse_Text_Npc1_3, 0, 0
    VMJump Daisy_Talked

Daisy_Give:
    VMStackPush 0x8000
    VMStackPush 0x8001
    WorkSetConst 0x8000, ITEM_TOWN_MAP
    WorkSetConst 0x8001, 1
    RTCallGlobal B2_SCRIPT_RECEIVE_ITEM
    VMStackPop 0x8001
    VMStackPop 0x8000
    FlagSet KANTO_FLAG_GOT_TOWN_MAP
    ParentActorMsg MSGFILE_SCRIPT, RivalsHouse_Text_Npc1_4, 0, 0
    VMJump Daisy_Talked

Daisy_Before:
    ParentActorMsg MSGFILE_SCRIPT, RivalsHouse_Text_Npc1_0, 0, 0

Daisy_Talked:
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt
    .balign 4, 0
