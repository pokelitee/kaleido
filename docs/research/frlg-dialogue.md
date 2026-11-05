# FireRed's dialogue on the path

Phase 3, step 2 (`docs/plan/08-phase3.md`, W2), run 2026-11-04 on the owner's machine with the owner's FireRed (USA,
revision 0, SHA1-checked). Question: can each map's messages be read from the player's FireRed by structure and shown
by Gen 5's text system, with nothing ROM-derived committed?

## Summary

- **Yes, for the path's nine maps.** The `gba_gen3_map_text` recipe kind reads 174 messages from FireRed's map
  scripts, converts them to Gen 5 text and appends them to the stand-in zones' text banks. Validation is clean and
  FireRed builds with them. **Verified** (§4).
- **Found by structure.** Nothing is looked up by address. The extractor finds the table of map groups, then each map's
  header by its group and number, the map's events and map scripts, and walks each script's bytecode to the messages
  it shows (§1).
- **IDs say where a message comes from, not what it says.** `OaksLab_Text_Npc4_0` is the first message of the lab's
  NPC 4. The scripts that W3 commits name messages this way, so they never carry FireRed's words.
- **No reflow is needed on this path.** FireRed's line and box breaks carry over as they are. Its widest line is
  narrower than 1% of Black 2's own lines, and its longest message fits the script's message buffer (§3).
- **Not carried over:** FireRed's text colors and voice fonts, which Gen 5's field text doesn't have. The other
  control codes FireRed uses elsewhere, such as music and pauses, are refused until a map needs them (§2).
- **On the stand-ins** (§5): FireRed's always-present people and its signs stand on Black 2's own NPC and sign spots,
  with talk scripts that show these messages. Story-flagged people and objects wait for the story step.

## 1. Finding the messages

The formats come from reading pret/pokefirered at `ce6406d8`. `framework/extractors/gba_gen3_maps.py`'s docstring
lists them; nothing was copied.

1. **The table of map groups.** It is the longest run of words that point to a table whose first word points to a map
   header. On the owner's ROM it finds 43 groups in 2.2 s. **Verified**.
2. **A map's header** is its group's table at its number. A group's table ends where the next one starts.
3. **Where scripts start**, in the ROM's order:
   - NPCs with a script;
   - triggers;
   - signs (hidden items are skipped);
   - map scripts, including the entries of their tables.
4. **The walk.** Each script is walked from its start. It follows jumps, calls, conditional ones, and the script that
   a trainer battle runs afterwards. It doesn't enter the numbered standard scripts, which hold generic messages.
   - **A message** is what the script loads into word 0 for the standard message script, what it shows directly, or
     a trainer battle's lines.
   - **Opcodes.** The walk knows the argument sizes of the 85 opcodes the nine maps use, and of the other jumps,
     calls and ends. Any other opcode stops it with an error rather than a guess.
5. **Order and ownership.** Messages are numbered in the order of the instructions that show them. A message that an
   earlier entry also shows belongs to that entry.

**E8's `map_ids` lists two extra maps for Pallet Town's section.** Its bottom-up search accepts another table shaped
like map groups, so section 0x58 also gives 0.0 and 0.2. **Verified** on the owner's ROM.
- Route 1's lookup is unaffected, since it gives only 3.19, so E8's and Phase 1's encounters stand.
- The walk above doesn't use that search.
- A fix, finding maps through `map_groups`, is a separate change.

## 2. Converting the text

| FireRed | Gen 5 | Evidence |
| --- | --- | --- |
| Characters | The same characters, UTF-8 | Gen 5's font 0 has a glyph for each one used, including `’ “ ” … é ♂ ♀` (`res/fonts/font/00/font.json`). **Verified** |
| Line break | `\n` | pokebw2's text format (`docs/data.md`, "Text") |
| Scroll a line | `{be00}\n` | Stream command 0 (category 0xBE) scrolls and 1 clears (`src/system/printsys.c`, `include/system/printsys.h` at the pin). Black 2's own text puts `\n` after each. **Verified** |
| New box | `{be01}\n` | As above |
| The player's name | `{0100:0}` | A word placeholder expands to its buffer's string whatever its type (`src/system/wordset.c`). Black 2's scripts fill buffer 0 with `WordSetPlayerName 0` (`aspertia_city.s`). **Verified** |
| The rival's name | `{0100:1}` | Black 2's scripts fill buffer 1 with `WordSetLoadRivalName 1`. **Verified**. How the rival gets a name is W4's |
| The script's strings 1 to 3 | `{0100:2}` to `{0100:4}` | The scripts W3 writes fill those buffers |
| Font change (voice fonts) | Dropped | FireRed's command 0x06 takes one byte (`GetExtCtrlCodeLength`, `src/string_util.c`). Gen 5's field text has no voice fonts |
| Other control codes | Refused | Viridian's Gym, outside the path, has music, pause and sound commands |

- **Wording is exact,** FireRed's capitals included ("POKéMON", "PROF. OAK"), as the feasibility table's "Dialogue
  wording" row says.
- **Text colors aren't carried over.** FireRed sets them per voice with a script command, not in the text.

## 3. Fit

Measured with Gen 5's font 0 advance widths, counting each name placeholder as seven of the widest capitals:

- **FireRed's lines on the path**: 594, the widest 193 px.
- **Black 2's script text lines**: 41,767. The 99th percentile is 223 px, so more than 400 of Black 2's own lines are
  wider than FireRed's widest. **Verified** (measurement).
- **Message length.** The longest message on the path is 388 characters of text file, fewer UTF-16 units than that.
  The script's message buffers hold 0x500 units (`src/ov012/script_work.c`). **Verified**.
- **Box height.** Gen 5's boxes, like FireRed's, hold two lines, and a scroll moves up one. That the converted breaks
  look right on screen is **Unverified** until the playtest.

## 4. On the owner's FireRed

| Location | Stand-in's bank | Messages |
| --- | --- | --- |
| `pallet_town` | `aspertia_city` | 19 |
| `players_house_1f` | `aspertia_city_3` | 7 |
| `players_house_2f` | `aspertia_city_4` | 3 |
| `rivals_house` | `aspertia_city_5` | 24 |
| `oaks_lab` | `aspertia_city_9` | 69 |
| `route_1` | `route_19` | 7 |
| `viridian_city` | `floccesy_town` | 29 |
| `viridian_mart` | `floccesy_town_3` | 8 |
| `viridian_pokemon_center` | `floccesy_town_pokemon_center` | 8 |

- **Beyond Phase 3's story.** The lab holds most of FireRed's later lab scenes too, such as Pokédex ratings and the
  national Pokédex. Phase 3's scripts use only what they need.
- **Shared scripts.** The Pokémon Center's and the Mart's clerks' lines come from FireRed's shared scripts. W3 may
  use B2W2's generic ones instead.
- **The rival's lab battle** is a trainer battle that carries the rival's two battle lines. They are among the lab's
  messages, until the trainer work moves them into Gen 5's trainer data.

**Verified** on the WSL clone:
- `./kaleido extract firered` writes nine text patches, deterministically from the ROM.
- `./kaleido validate firered` is clean. The merged banks keep Black 2's messages and end with FireRed's, before their
  `\pad` line.
- The build results are in `docs/status.md`.

## 5. Showing them on the stand-ins

Added 2026-11-04. The FRLG family puts FireRed's people and signs on the stand-ins, with scripts that show their
messages (`content/families/frlg/res/field/`). It is a stand-in arrangement (D1), replaced when a map gets its own art.

- **Places come from Black 2.** Each person or sign takes one of Black 2's own NPC or sign spots on the same stand-in:
  its position, height, movement, facing and area. Black 2 put an actor there, so it can stand there and be reached.
  The two house name signs are the exception. Pallet Town's doors have no Black 2 sign beside them, so each sign is
  two tiles left of its door, where Black 2 puts its own house sign beside the player's door.
- **Who is placed.** The people whom FireRed shows without a story flag, 22 of them, and 12 signs. Left for the story
  step (W3):
  - those a flag hides or shows: Oak, twice; the rival in the lab; the starter balls, the Pokédexes, the Town Map; the
    trees that Cut clears; an item;
  - signs with no spot on their stand-in: the houses' TV, PC, posters and shelves, and two of Viridian's Trainer Tips.
- **Each script shows one line.** People whose FireRed scripts branch show the line that fits a first visit, picked by
  hand. Mom's two lines, for a boy or a girl, go through `ActorMsgGendered`, which picks the second message for a
  female player (`src/ov036/scrcmd_msg.c`). **Verified**.
- **Message boxes follow Black 2's own scripts.** People speak with `ParentActorMsg`. Outdoor signs use
  `MsgPlaceSign` with Black 2's boards: 1 for a town, 2 for a building, 3 for a route, 0 for Trainer Tips. Indoor
  objects use `InfoMsg`. Names are filled as §2 says.
- **Models are placeholders**, chosen from what Black 2 itself uses them for:
  - the nurse is `OBJ_CODE_78`, the model of the nurse who runs Black 2's healing script (global 2100);
  - the clerks are `OBJ_CODE_77`, the Pokémon Center's Mart clerks;
  - Mom is `OBJ_CODE_NURSERY_AIDE`, the mother in the house that stands in for the player's;
  - the others are named trainer classes or townsfolk of Black 2's that look the part.

  Oak and the rival, when the story step places them, will use Juniper's model (`OBJ_CODE_105`, D3) and Hugh's
  (`OBJ_CODE_291`).
- **Loading other models.** A zone's NPC cache holds at most 26 models' records. The field reads any other model's
  record from the model table (pokebw2's `docs/data.md`, "NPC info cache"), so a stand-in can show models it never
  had. That this costs no visible delay is **Unverified** until the playtest.
- **Scripts replace the stand-ins' script files.** No other zone shares one, and no C code starts their scripts. The
  only C reader of one of their text banks, the starter selection reading Aspertia's, uses Black 2's messages, which
  stay. **Verified** at the pin.
- **Validation now checks event scripts.** `kaleido validate` checks that every NPC's, sign's and trigger's script
  below 2000 is an entry of its zone's script file. Global scripts start at 2000 (pokebw2's `docs/scripts.md`), and
  Black 2's own events pass.
