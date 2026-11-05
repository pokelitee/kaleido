#include "asm/field_script.inc"
#include "text/script/aspertia_city_9.h"

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntry Script_4
    ScriptEntry Script_5
    ScriptEntry Script_6
    ScriptEntriesEnd

Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc1_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_2:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc2_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_3:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    WordSetPlayerName 0
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc3_0, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_4:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    InfoMsg OaksLab_Text_Sign0_0, 2
    LastKeyWait
    InfoMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_5:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    InfoMsg OaksLab_Text_Sign2_0, 2
    LastKeyWait
    InfoMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

Script_6:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    InfoMsg OaksLab_Text_Sign3_0, 2
    LastKeyWait
    InfoMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt
    .balign 4, 0
