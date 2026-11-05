#include "asm/field_script.inc"
#include "text/script/aspertia_city_3.h"
#include "frlg_story.inc"

    ScriptEntry Script_1
    ScriptEntriesEnd

// Mom: before the player has a Pokémon, her line for a boy or a girl; after, she heals the party, as Black 2's mother
// does at home
Script_1:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_HAS_STARTER, Mom_NoPokemon
    WordSetPlayerName 0
    ParentActorMsg MSGFILE_SCRIPT, PlayersHouse1f_Text_Npc1_2, 0, 0
    LastKeyWait
    ActorMsgClose
    FadeEx 3, 0, 16, 2
    FadeExWait
    PokePartyRecoverAll
    MEPlay SEQ_ME_ASA
    MEWait
    FadeEx 3, 16, 0, 2
    FadeExWait
    ParentActorMsg MSGFILE_SCRIPT, PlayersHouse1f_Text_Npc1_3, 0, 0
    VMJump Mom_Talked

Mom_NoPokemon:
    ActorMsgGendered MSGFILE_SCRIPT, PlayersHouse1f_Text_Npc1_0, PlayersHouse1f_Text_Npc1_1, 1, 0, 0

Mom_Talked:
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt
    .balign 4, 0
