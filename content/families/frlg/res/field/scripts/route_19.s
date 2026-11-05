#include "asm/field_script.inc"
#include "text/script/route_19.h"

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntriesEnd

Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, Route1_Text_Npc1_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_2:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, Route1_Text_Npc2_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_3:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    MsgPlaceSign Route1_Text_Sign0_0, 3
    MsgPlaceSignClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt
    .balign 4, 0
