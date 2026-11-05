#include "asm/field_script.inc"
#include "text/script/floccesy_town.h"

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntry Script_4
    ScriptEntry Script_5
    ScriptEntry Script_6
    ScriptEntry Script_7
    ScriptEntry Script_8
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

Script_3:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc4_4, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_4:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, ViridianCity_Text_Npc5_1, 0, 0
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
    .balign 4, 0
