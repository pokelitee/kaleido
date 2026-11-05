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
- **Not on screen yet.** No script names these messages until the next pieces of step 2 and W3 add NPCs, signs and
  scripts to the stand-ins.

## 1. Finding the messages

The formats come from reading pret/pokefirered at `ce6406d8`. The docstrings of `framework/extractors/gba_gen3.py`
(map headers and groups) and `gba_gen3_maps.py` (the rest) list them; nothing was copied.

1. **The table of map groups.** It is the longest run of words that point to a table whose first word points to a map
   header. On the owner's ROM it finds 43 groups in 2.2 s. **Verified**.
2. **A map's header** is its group's table at its number. A group's table ends where the next one or the table of
   groups starts.
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

**E8's `map_ids` listed two extra maps for Pallet Town's section; fixed.** Its bottom-up search accepted another table
shaped like map groups, so section 0x58 also gave 0.0 and 0.2. It now reads the maps of the table of map groups (step
1) and keeps those in the section, so 0x58 gives 3.0 and 4.0 to 4.3. **Verified** on the owner's ROM, 2026-11-04.
- Route 1's lookup gave only 3.19 before and after. E8's and Phase 1's encounters stand: the extracted table is
  unchanged (`488c6a6c…`).
- The table of groups starts right after the last group's table. Its pointers to groups' tables also pass for
  pointers to map headers, and would add 43 maps to group 42, so a group's table ends there too. **Verified**.

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
