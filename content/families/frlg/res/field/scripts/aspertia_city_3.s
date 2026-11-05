#include "asm/field_script.inc"
#include "text/script/aspertia_city_3.h"

    ScriptEntry Script_1
    ScriptEntriesEnd

Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    ActorMsgGendered MSGFILE_SCRIPT, PlayersHouse1f_Text_Npc1_0, PlayersHouse1f_Text_Npc1_1, 1, 0, 0
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt
    .balign 4, 0
