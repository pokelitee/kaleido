#include "asm/field_script.inc"
#include "text/script/route_19.h"
#include "frlg_story.inc"

    ScriptEntry Script_1
    ScriptEntry Script_2
    ScriptEntry Script_3
    ScriptEntriesEnd

// The Poké Mart clerk with the sample Potion: given once, if the bag has room
Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    KantoUnlessFlag KANTO_FLAG_GOT_POTION, Clerk_Pitch
    VMJump Clerk_Reminder

Clerk_Pitch:
    ParentActorMsg MSGFILE_SCRIPT, Route1_Text_Npc1_0, 0, 0
    LastKeyWait
    ActorMsgClose
    ItemCheckSpace ITEM_POTION, 1, 0x8010
    KantoUnlessEqual 0x8010, 0, Clerk_GivePotion
    ParentActorMsg MSGFILE_SCRIPT, Route1_Text_Npc1_4, 0, 0
    VMJump Clerk_Talked

Clerk_GivePotion:
    ItemAdd ITEM_POTION, 1, 0x8010
    WordSetItemName 3, ITEM_POTION
    MEPlay SEQ_ME_ITEM
    SystemMsg Route1_Text_Npc1_1, 1
    MEWait
    MsgWaitAdvance
    SystemMsgClose
    WordSetPlayerName 0
    SystemMsg Route1_Text_Npc1_2, 1
    MsgWaitAdvance
    SystemMsgClose
    FlagSet KANTO_FLAG_GOT_POTION

Clerk_Reminder:
    ParentActorMsg MSGFILE_SCRIPT, Route1_Text_Npc1_3, 0, 0

Clerk_Talked:
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
