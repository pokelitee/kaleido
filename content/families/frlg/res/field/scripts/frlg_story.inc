// The FRLG family's story state, in saved event flags and variables that no Black 2 script, event or C source names
// (docs/status.md, Phase 3 step 3), and the comparisons its scripts make

// Where the story is
#define KANTO_VAR_STORY 0x404E
#define KANTO_STORY_NEW_GAME 0
// Oak has brought the player to his lab
#define KANTO_STORY_IN_LAB 1
// The player and the rival have their starters
#define KANTO_STORY_HAS_STARTER 2
// The rival's lab battle is over
#define KANTO_STORY_RIVAL_BATTLED 3
// The Viridian Mart's clerk has given the player Oak's Parcel
#define KANTO_STORY_HAS_PARCEL 4
// The parcel is delivered, and Oak has given the Pokédex and Poké Balls
#define KANTO_STORY_HAS_POKEDEX 5

// The starter the player chose on the starter screen: 0 Bulbasaur, 1 Charmander, 2 Squirtle
#define KANTO_VAR_STARTER 0x404F

// Set while an actor is away; an NPC whose spawn flag is set doesn't appear
#define KANTO_FLAG_HIDE_PALLET_OAK 0x01F2
#define KANTO_FLAG_HIDE_LAB_OAK 0x01F3
#define KANTO_FLAG_HIDE_LAB_RIVAL 0x01F4
#define KANTO_FLAG_GOT_POTION 0x01F5
#define KANTO_FLAG_GOT_TOWN_MAP 0x01F6

// Black 2's flags for having a Pokémon and the Pokédex, which its own starter scene sets
#define B2_FLAG_HAS_POKEMON EVENT_FLAG_0x0961
#define B2_FLAG_HAS_POKEDEX EVENT_FLAG_0x0962

// Black 2's global scripts: the Poké Mart, with the shop list in 0x8000 (255 the standard one) and 1 in 0x8001; and
// receiving an item, with the item in 0x8000 and the count in 0x8001
#define B2_SCRIPT_MART 10110
#define B2_SCRIPT_RECEIVE_ITEM 2805
#define B2_MART_STANDARD 255

// Jumps unless the variable's value compares as named. VMJumpIf CMP_STACK jumps when the comparison is false
// (scrcmd_vm.c), so each macro jumps past the code that runs when it holds
    .macro KantoUnlessEqual var, value, label
    VMStackPush \var
    VMStackPushConst \value
    VMStackCmp CMP_EQ
    VMJumpIf CMP_STACK, \label
    .endm

    .macro KantoUnlessAtLeast var, value, label
    VMStackPush \var
    VMStackPushConst \value
    VMStackCmp CMP_GE
    VMJumpIf CMP_STACK, \label
    .endm

    .macro KantoUnlessFlag flag, label
    VMStackPushFlag \flag
    VMStackPushConst 1
    VMStackCmp CMP_EQ
    VMJumpIf CMP_STACK, \label
    .endm
