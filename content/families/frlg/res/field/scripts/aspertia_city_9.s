#include "asm/field_script.inc"
#include "text/script/aspertia_city_9.h"
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
    ScriptEntry Script_10
    ScriptEntry Script_11
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

// Oak: with the parcel, its delivery; before, a word on raising the starter; after, his send-off
Script_7:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    WordSetPlayerName 0
    WordSetLoadRivalName 1
    KantoUnlessEqual KANTO_VAR_STORY, KANTO_STORY_HAS_PARCEL, Lab_OakNoParcel
    VMJump Lab_Delivery

Lab_OakNoParcel:
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_HAS_POKEDEX, Lab_OakRaise
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_30, 0, 0
    VMJump Lab_OakTalked

Lab_OakRaise:
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_10, 0, 0

Lab_OakTalked:
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// The parcel's delivery: Oak takes it, the rival comes back, and Oak gives both of them a Pokédex (as Black 2's own
// starter scene gives it) and the player five Poké Balls
Lab_Delivery:
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_11, 0, 0
    LastKeyWait
    ActorMsgClose
    ItemSub ITEM_PARCEL, 1, 0x8010
    SystemMsg OaksLab_Text_Npc4_12, 1
    MsgWaitAdvance
    SystemMsgClose
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_13, 0, 0
    LastKeyWait
    ActorMsgClose
    FlagReset KANTO_FLAG_HIDE_LAB_RIVAL
    ActorAdd 8
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_14, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_15, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_16, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_17, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_18, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    FlagSet B2_FLAG_HAS_POKEDEX
    MEPlay SEQ_ME_KEYITEM
    TrainerCardGetSex 0x8010
    KantoUnlessEqual 0x8010, 0, Lab_DexFemale
    PlayFieldEffect 63
    VMJump Lab_DexShown

Lab_DexFemale:
    PlayFieldEffect 64

Lab_DexShown:
    WordSetPlayerName 0
    SystemMsg OaksLab_Text_Npc4_19, 1
    MEWait
    MsgWaitAdvance
    SystemMsgClose
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_20, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ItemAdd ITEM_POKE_BALL, 5, 0x8010
    MEPlay SEQ_ME_ITEM
    SystemMsg OaksLab_Text_Npc4_21, 1
    MEWait
    MsgWaitAdvance
    SystemMsgClose
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_22, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_23, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_24, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc4_25, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorDelete 8
    FlagSet KANTO_FLAG_HIDE_LAB_RIVAL
    WorkSetConst KANTO_VAR_STORY, KANTO_STORY_HAS_POKEDEX
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// The rival
Script_8:
    ActorsPauseAll
    SEPlay SEQ_SE_MESSAGE
    ActorSetEyeToEye
    WordSetPlayerName 0
    WordSetLoadRivalName 1
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_HAS_STARTER, Lab_RivalBeforeStarter
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc8_2, 0, 0
    VMJump Lab_RivalTalked

Lab_RivalBeforeStarter:
    ParentActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc8_0, 0, 0

Lab_RivalTalked:
    LastKeyWait
    ActorMsgClose
    FinishAllEvents
    ActorsUnpauseAll
    VMHalt

// When Oak has brought the player in: the rival is named (D9), Oak offers the three, the player chooses on Black 2's
// starter screen (D8), and the rival takes the one strong against the player's
Script_9:
    ActorsPauseAll
    FadeOutBlackQ
    FadeWait
    CallRivalNameInput 0x8010
    FadeInBlackQ
    FadeWait
    WordSetPlayerName 0
    WordSetLoadRivalName 1
    SEPlay SEQ_SE_MESSAGE
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_MapScript2_0, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_MapScript2_1, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_MapScript2_2, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_MapScript2_3, 4, 0, 0
    LastKeyWait
    MsgWinCloseAll
    WorkSetConst 0x8024, 0
    FadeOutBlackQ
    FadeWait
    FieldClose
    callPoke3Select 0x8024
    FieldOpen
    FadeInWhiteQ
    FadeWait
    WorkSet KANTO_VAR_STARTER, 0x8024
    KantoUnlessEqual 0x8024, 0, Lab_NotBulbasaur
    WorkSetConst 0x8025, SPECIES_BULBASAUR
    WorkSetConst 0x8026, SPECIES_CHARMANDER
    VMJump Lab_StarterChosen

Lab_NotBulbasaur:
    KantoUnlessEqual 0x8024, 1, Lab_Squirtle
    WorkSetConst 0x8025, SPECIES_CHARMANDER
    WorkSetConst 0x8026, SPECIES_SQUIRTLE
    VMJump Lab_StarterChosen

Lab_Squirtle:
    WorkSetConst 0x8025, SPECIES_SQUIRTLE
    WorkSetConst 0x8026, SPECIES_BULBASAUR

Lab_StarterChosen:
    WordSetPlayerName 0
    WordSetPokeSpecies 2, 0x8025
    MEPlay SEQ_ME_POKEGET
    SystemMsg OaksLab_Text_Npc5_5, 1
    MEWait
    MsgWaitAdvance
    SystemMsgClose
    PokePartyAdd 0x8010, 0x8025, 0, 5
    FlagSet B2_FLAG_HAS_POKEMON
    SystemMsg OaksLab_Text_Npc5_6, 1
    YesNoWin 0x8010
    SystemMsgClose
    // YesNoWin gives 0 for yes (scrcmd_menu.c)
    KantoUnlessEqual 0x8010, 0, Lab_NoNickname
    FadeOutBlackQ
    FadeWait
    CallPokeNameInput 0x8010, 0, 0
    FadeInBlackQ
    FadeWait

Lab_NoNickname:
    WordSetLoadRivalName 1
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Npc5_7, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    WordSetPokeSpecies 2, 0x8026
    MEPlay SEQ_ME_POKEGET
    SystemMsg OaksLab_Text_Npc5_8, 1
    MEWait
    MsgWaitAdvance
    SystemMsgClose
    WorkSetConst KANTO_VAR_STORY, KANTO_STORY_HAS_STARTER
    ActorsUnpauseAll
    VMHalt

// The rival's challenge as the player leaves with a starter: a battle with the trainer whose starter is strong against
// the player's, which the player may lose and go on, as in Black 2's own first rival battle, then healing
Script_10:
    ActorsPauseAll
    WordSetPlayerName 0
    WordSetLoadRivalName 1
    SEPlay SEQ_SE_MESSAGE
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Trigger3_0, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    KantoUnlessEqual KANTO_VAR_STARTER, 0, Lab_RivalNotCharmander
    CallTrainerBattle TRAINER_RIVAL, 0, 1
    VMJump Lab_RivalBattled

Lab_RivalNotCharmander:
    KantoUnlessEqual KANTO_VAR_STARTER, 1, Lab_RivalBulbasaur
    CallTrainerBattle TRAINER_RIVAL_2, 0, 1
    VMJump Lab_RivalBattled

Lab_RivalBulbasaur:
    CallTrainerBattle TRAINER_RIVAL_3, 0, 1

Lab_RivalBattled:
    CallTrainerBattleEnd
    PokePartyRecoverAll
    WordSetPlayerName 0
    WordSetLoadRivalName 1
    ActorMsg MSGFILE_SCRIPT, OaksLab_Text_Trigger3_3, 8, 0, 0
    LastKeyWait
    MsgWinCloseAll
    ActorDelete 8
    FlagSet KANTO_FLAG_HIDE_LAB_RIVAL
    WorkSetConst KANTO_VAR_STORY, KANTO_STORY_RIVAL_BATTLED
    ActorsUnpauseAll
    VMHalt

// On loading: Oak is in once he has brought the player, and the rival until he leaves after the battle
Script_11:
    KantoUnlessEqual KANTO_VAR_STORY, KANTO_STORY_NEW_GAME, Lab_OakIn
    FlagSet KANTO_FLAG_HIDE_LAB_OAK
    VMJump Lab_OakPlaced

Lab_OakIn:
    FlagReset KANTO_FLAG_HIDE_LAB_OAK

Lab_OakPlaced:
    KantoUnlessAtLeast KANTO_VAR_STORY, KANTO_STORY_RIVAL_BATTLED, Lab_RivalIn
    FlagSet KANTO_FLAG_HIDE_LAB_RIVAL
    VMJump Lab_RivalPlaced

Lab_RivalIn:
    FlagReset KANTO_FLAG_HIDE_LAB_RIVAL

Lab_RivalPlaced:
    VMHalt
    .balign 4, 0
