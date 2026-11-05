# FireRed's trainers on the path

Phase 3, step 2 (`docs/plan/08-phase3.md`, W2), run 2026-11-04 on the owner's machine with the owner's FireRed (USA,
revision 0, SHA1-checked). Question: can a FireRed trainer's party, prize and battle lines be read by structure and
carried onto a Gen 5 trainer?

## Summary

- **Yes, for the rival's three Oak's Lab battles.** The `gba_gen3_trainers` recipe kind patches Black 2's three first
  rival battles (`TRAINER_RIVAL`, `_2`, `_3`) with FireRed's trainers 326 to 328. Each gets its level 5 starter, the
  prize and its two battle lines. Validation is clean and FireRed builds with them. **Verified** (§4).
- **Found by structure.** The trainers' table and the prize money table are found by their shape. The battle lines
  come from the battle that the lab's scripts start with each trainer, found by the script walk of
  `frlg-dialogue.md` §1.
- **Party, IVs and prize carry over exactly.**
  - FireRed and Gen 5 make IVs from a trainer Pokémon's IV level the same way.
  - Both pay 4 × the last Pokémon's level × a multiplier, so FireRed's class multiplier becomes Gen 5's `money`.
- **Kept from Black 2: the name, class, sprite and AI.** The rival shows as Black 2's rival, Hugh, until trainer art
  and the rival's name are scheduled (D3, W4). Gen 5's AI replaces FireRed's (`01-feasibility.md`).
- **Not handled yet:** items, held or used, which need a Gen 3 to Gen 5 item mapping, and species past 251. Both are
  refused with an error rather than guessed. The rival's lab parties have neither.

## 1. Finding the trainers

The formats come from reading pret/pokefirered at `ce6406d8`. `framework/extractors/gba_gen3_trainers.py`'s docstring
lists them; nothing was copied.

- **The table.** It is the longest run of 40-byte records with a possible party: kind, size 1 to 6, and a pointer.
  The empty record before the run is trainer 0. The owner's ROM has 743 trainers (0 to 742) at `0x23eac8`.
  **Verified**.
- **A party member** is 8 bytes, or 16 with moves, as agbcc pads them. 404 of the owner's ROM's parties have two or
  more Pokémon and no items or moves. All 404 fit 8-byte members; only 54 fit 6. **Verified**.
- **The prize money table** has 4-byte entries: a class and its multiplier, ended by class 0xFF, whose multiplier is
  the default. The owner's ROM has 104 classes. The rival's class has 4 and a Gym Leader's 25, as pret's table says.
  **Verified**.

## 2. Converting a trainer

| FireRed | Gen 5 | Evidence |
| --- | --- | --- |
| Species 1 to 251 | `SPECIES_*` by number | The national order, as E8's encounters |
| Level | `level` | |
| IV level | `difficulty` | Each IV is the level × 31 / 255 in both: `CreateNPCTrainerParty` (pret) and `tr_tool.c` (pokebw2). **Verified** |
| Custom moves | `moves` by number | Moves 1 to 354 have the same numbers in both. pret's constants and pokebw2's `moves.txt` agree on all 354, three only spelled differently. **Verified** |
| Class multiplier, doubled for a double battle | `money` | The prize is 4 × the last Pokémon's level × the multiplier, × 2 in a double battle (`GetTrainerMoneyToGive`). Gen 5's is 4 × that level × `money` (`btl_calc.c`). **Verified** |
| Double battle flag | `battle_style` | |
| Line before the battle | `TRMSG_START` | `trainer_messages.h` |
| Line on losing | `TRMSG_LOSE` | |
| Line on winning (the early rival's battle) | `TRMSG_WIN` | |
| Held items, trainer items | Refused | No item mapping yet |
| Sex and ability | `gender` and `ability` 0: from the Pokémon's personality, as in FireRed | Natures and abilities can differ, since Gen 5 seeds the personality differently. **Assumption** |

Battle lines become trainer JSON's text with real line breaks. Gen 5 trainer messages use `{be00}` and `{be01}`
(Black 2 has 302 and 1,251 of them), so breaks carry over as `frlg-dialogue.md` §2 says.

**No Black 2 trainer message has a name placeholder.** The rival's winning line starts with the rival's name, so
whether a battle fills `{0100:1}` is **Unverified** until the playtest.

## 3. Black 2's rival battles as stand-ins

Black 2's first rival battle has a trainer for each starter Hugh can take. FireRed's lab battle has one for each
starter the rival takes. Each FireRed trainer goes on the Black 2 trainer whose starter shares its type:

| Gen 5 trainer | Black 2 starter | FireRed trainer | Rival's starter |
| --- | --- | --- | --- |
| `TRAINER_RIVAL` | Tepig | 328 | Charmander |
| `TRAINER_RIVAL_2` | Oshawott | 326 | Squirtle |
| `TRAINER_RIVAL_3` | Snivy | 327 | Bulbasaur |

- **Nothing starts these battles yet.** Step 1 took Black 2's Aspertia scenes out of the stand-ins, and step 3's lab
  script will start the battle.
- **The Route 22 and later rival battles** are outside Phase 3 (`08-phase3.md`).

## 4. On the owner's FireRed

**Verified** on the WSL clone:
- `./kaleido extract firered` writes the three patches. Each is a level 5 starter with IV level 0, no moves or items,
  `money` 4 (a prize of 80 for a level 5 Pokémon, as FireRed pays), and the losing and winning lines.
- `./kaleido validate firered` is clean, including the schema check on the merged trainers. They keep Black 2's name,
  class and AI.
- FireRed builds. pokebw2's `tools/data/trainer_data.py dump` of the built archives reads the three parties, the
  prize and both lines back from the ROM's own files. Build hashes are in `docs/status.md`.
