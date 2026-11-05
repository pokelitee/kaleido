#include "asm/field_script.inc"
#include "text/script/aspertia_city.h"
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
    ParentActorMsg MSGFILE_SCRIPT, PalletTown_Text_Npc1_2, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_2:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, PalletTown_Text_Npc2_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_3:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign PalletTown_Text_Sign0_0, 2
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_4:
    ActorsPauseAll
    WordSetPlayerName 0
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign PalletTown_Text_Sign1_0, 2
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_5:
    ActorsPauseAll
    WordSetLoadRivalName 1
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign PalletTown_Text_Sign2_0, 2
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_6:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign PalletTown_Text_Sign3_0, 1
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_7:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign PalletTown_Text_Sign4_0, 0
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// Oak's escort (D7): he calls out as the player heads for the route, comes up and warns them, then a fade takes both to
// his lab
Script_8:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    InfoMsg PalletTown_Text_Trigger0_0, 2
    LastKeyWait
    InfoMsgClose
    FlagReset KANTO_FLAG_HIDE_PALLET_OAK
    ActorAdd 3
    PlayerGetGPos 0x8021, 0x8022
    ActorWalkRoute 3, 0x8021, 0x8022, 1, 8, 0
    ActorCmdWait
    ActorMsg MSGFILE_SCRIPT, PalletTown_Text_Trigger0_1, 3, 0, 0
    MsgWinCloseAll
    FadeOutBlack
    FadeWait
    ActorDelete 3
    FlagSet KANTO_FLAG_HIDE_PALLET_OAK
    WorkSetConst KANTO_VAR_STORY, KANTO_STORY_IN_LAB
    // Inside the lab's door, facing up (DIR_UP)
    MapChangeWarp ZONE_ASPERTIA_CITY_9, 9, 23, 0
    ActorsUnpauseAll
    VMHalt

// On loading: Oak is only in town for his escort
Script_9:
    FlagSet KANTO_FLAG_HIDE_PALLET_OAK
    VMHalt
    .balign 4, 0
