#include "asm/field_script.inc"
#include "text/script/aspertia_city.h"

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntry Script_4
    ScriptEntry Script_5
    ScriptEntry Script_6
    ScriptEntry Script_7
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
    .balign 4, 0
