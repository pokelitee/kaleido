# E5 — Species #650 end to end

Phase 0 experiment (`docs/plan/05-roadmap.md`), run 2026-11-03 on the owner's machine in the scratch checkout
`~/kaleido-work/pokebw2` at pokebw2 `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c` (branch `phase0-e5`, on top of E3's
`--define` and E4a's dsd flags). Question: what does adding a species past Genesect cost, and where are the limits
(R-14)?

## Summary

- **A species inserted after Genesect, as #650, builds into every archive a species needs.** Its data, name, Pokédex
  text, sprites, icon, musical sprites, footprint, cry and cry volume, Pokédex order entries and a Route 19 encounter
  slot all read back from the built ROM. Every later species, the egg and the Pokéstar species keep their own files at
  their shifted places. **Verified** (§5).
- **One-time engine cost: about 40 numbers in 10 engine files and 3 packers**, all derived from the species list in
  [`e5-species-expansion.patch`](e5-species-expansion.patch). With the stock list the build still matches Black 2 byte
  for byte with every check. **Verified** (§2).
- **Two packers can't add a species**, for the same reason E4b found for map art: they edit the extracted archives file
  by file. The patch gives them a template splice: an added species starts as a copy of a named stock species' files,
  which its own sources then edit (§3).
- **Per species**: one line in `generated/species.txt`, a `res/pokemon/<species>/` directory, two sound list lines and
  a bank, seven Pokédex order entries and one byte in a C table (§4).
- **Capacity**: 672 national species fit the Pokédex save as it is (23 past Genesect); past that, the save block grows.
  Other fields allow 1023 or more (§7).
- **Known gaps, not fixed here**: Box Search and the GTS hard-code each letter's place in the alphabetical list, and
  easy-chat words are numbered after the species (§8). Tier 1 doesn't need species past 649.
- **Found on the way: upstream's incremental build can link stale objects** after a generated header changes, and still
  produce a ROM without error (new risk R-28, §6).
- The in-game check (catch it, see it in the Pokédex, save, reload) is deferred to the playtest pass.

## 1. How species are numbered

All **Verified** in pokebw2's sources and packers at the pin:

- `generated/species.txt` sets every species' number: `SPECIES_NONE`, the national Pokédex's 649, then `SPECIES_EGG`
  (650), `SPECIES_BAD_EGG` (651) and 33 Pokéstar Studios species (652–684).
- The packers count the national Pokédex as "the species before `SPECIES_EGG`" (`species_data.py`,
  `pokemon_graphics.py`, `personal_bw1_data.py`), so inserting after Genesect is the path the tooling already supports.
  It renumbers the egg, the bad egg and the Pokéstar species.
- Battle sprites, icons and cries have slots after the species': the egg's sprites and icon at 683, form sprites from
  685; cries are wave archives 1–684 by species number, then form cries 685–690.
- Species data, level-up moves, evolutions, baby species, egg moves, Black and White's species data and the Pokédex
  tables are built from the species list. The sprite and cry-volume archives are not (§3).

## 2. Numbers derived from the species list

The patch replaces each number below with an expression of the species constants. Each keeps its operator and value
with the stock list, so the compiled code doesn't change. **Verified**: full `ninja` with every matching check passes
with SHA1 `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`, both with these changes alone and with the packer changes of §3
(13 files, +82/−42 lines).

| Where | Was | Now | What it is |
| --- | --- | --- | --- |
| `pokedex_savedata.c` | `SPECIES_GENESECT` (8 uses) | `SPECIES_EGG - 1` | Valid species for the Pokédex, and its count loops |
| `pokedex_list_main.h` | `649` | `SPECIES_EGG - 1` | National list length (also sizes a name array, 4 B per species) |
| `pokedex_search_engine.c` | `649`, `650` | `SPECIES_EGG - 1`, `SPECIES_EGG` | Search over the national Pokédex |
| `day_care.c` | `SPECIES_GENESECT` (2) | `SPECIES_EGG - 1` | TM inheritance check, baby lookup. Keeps the original's `>=`, which excludes the last national species |
| `scrcmd_leaves.c` | `SPECIES_GENESECT` | `SPECIES_EGG - 1` | Species past the national Pokédex |
| `resonance_resort_data.c` | `650` | `SPECIES_EGG` | Join Avenue's egg |
| `musical_mcss.c` | `650` | `SPECIES_EGG` | The musical's egg sprite group |
| `pokegra.c` | `683`, `0x3584`, `0x3ab9` | from `SPECIES_POKESTAR_SMEARGLE_2` | Battle sprites of the egg, the forms and the form palettes |
| `poke_icon.c` | `683`, `685`, `685`, `686` | from `SPECIES_POKESTAR_SMEARGLE_2` | Icons and icon palettes of the egg and the forms |
| `pm_voice.c` | `684`, `652`, `685`–`690` | `SPECIES_POKESTAR_SMEARGLE_2`, `SPECIES_POKESTAR_UFO`, `+1`…`+6` | Last cry by species, first cry played by number, form cries |
| `pokemon_graphics.py` | `(683, 685)`, `(650, 652)` (3 uses), `14240`, `15020`, `14253`, `15033` | from the species list | Sprite groups of the egg and forms; where the Substitute and Arceus palettes start |
| `sound_data.py` | `range(1, 691)` | from the species list and the cry forms | Which wave archives are cries |

The last Pokéstar constant stands for "the list's end" because the generated species header has no count constant.
Phase 1 would add one (`gen_constants.py`).

Extraction-time tools (`make_constants.py`'s 685 and Pokéstar range, `pokemon_cries.py`'s export range) still describe
the stock ROM, which is right: they read it.

## 3. Packers that couldn't add a species

`pokemon_graphics.py` (battle sprites `a/0/0/4`, icons `a/0/0/7`, musical sprites `a/0/5/1`, footprints `a/1/6/5`) and
`pokemon_cries.py` (cry volumes `a/1/9/1`) start from the extracted archive and patch each file in place. With a
species inserted, every file after #650 lined up with the wrong source, and the first build stopped on a missing
`pokestar/white_door/icon_female.png`. **Verified**.

The patch adds `with_added_species()`: before patching, each added species gets a copy of its template's files at its
place (20 battle sprite files, 2 icons, 20 musical files, 1 footprint, 1 volume entry). `res/pokemon/<species>/template.txt`
names the template, which must be a stock species. The species' own PNGs and palettes then edit the copy, as for any
species. With no species added, nothing changes (the matching build in §2).

This is ADR 0003's template-append again, at species level. New sprite art has to fit the template's cells and
animation files. Whether that's enough for real new species is **Unverified**: E5 used Audino's art unchanged.

## 4. The test species

| Piece | What |
| --- | --- |
| `SPECIES_KALEIDOMON` | Line after `SPECIES_GENESECT` in `generated/species.txt`: #650; the egg becomes 651 |
| `res/pokemon/kaleidomon/` | Audino's directory (sprites, musical sprites, icon, footprint, `cry.wav`), with its own name, base stats 111/99/88/77/66/55, Steel/Psychic, Pokédex category and entry, `regional_dex_number` 0, and `template.txt` = `audino` |
| Cry | `WAVE_ARC_PV650_KALEIDO` and `BANK_PV650_KALEIDO` inserted at 650 in the sound lists (the cries end at 691; the next constant is fixed at 1000), bank copied from Audino's |
| Icon palette | Audino's byte inserted at 650 in `sPokeIconPalettes` (`poke_icon.c`), a C table with one entry per species |
| Pokédex orders | `res/pokedex/orders.json`: after Genesect (national, regional), after Kakuna (alphabetical), after Audino (four size lists) |
| Encounter | Route 19's first grass slot (20%): Kaleidomon, level 3 |

Never committed: the art and cry are Black 2's.

## 5. Verified in the built ROM

ROM target with `--allow-stale-secure-area` (the icon table and the derived constants change ARM9 main); incremental
rebuild 134 s. Archives read back (`build/b2_us/files`):

| Archive | Built | Original |
| --- | --- | --- |
| Species data `a/0/1/6` | 711 | 710 |
| Level-up moves `a/0/1/8`, evolutions `a/0/1/9` | 710 | 709 |
| Baby species `a/0/2/0` | 686 | 685 |
| Egg moves `a/1/2/4` | 651 | 650 |
| Cry volumes `a/1/9/1` | 686 | 685 |
| Black and White species data `a/3/0/2` | 670 | 669 |
| Battle sprites `a/0/0/4` | 15,085 | 15,065 |
| Icons `a/0/0/7` | 1,512 | 1,510 |
| Musical sprites `a/0/5/1` | 14,305 | 14,285 |
| Footprints `a/1/6/5` | 656 | 655 |
| Pokédex areas `a/1/7/6` | 685 | 684 |

- #650's sprite, icon, musical and footprint files equal Audino's; every file after them equals the original's from
  the old #650 on.
- `species_data.py dump` of the built archives gives back Kaleidomon's name, stats, types, Pokédex category and entry,
  and the egg's record at its new place.
- Sound archive: wave archive 650 holds the same file as Audino's (531).
- Route 19's encounter table: first grass slot species 650, levels 3–3 (was 504 Patrat, 2–2).
- `verify_dsi_rom.py`: every check it runs passes (281,268 DS-area and 421 DSi-area sector digests, 8,803 block
  digests, every HMAC but the secure area's, which it skips by design).
- Test ROM SHA1 `186daf98390e58cd16a8d9b9bebd58e1b2915fab` (`~/kaleido-work/e5/kaleido-e5-test.nds`, never committed).
  A rebuild that ran ninja until nothing was left to compile gave the same SHA1, so its objects are consistent (§6).

## 6. Stale objects after a generated header changes

The first try at the stock-list check above failed: 265 of 350 module checks, including ARM9 main, ITCM and DTCM. Only
one C file had recompiled. **Verified** cause, in upstream's build at the pin:

- `mwccarm` writes depfiles with absolute paths, which `fix_depfile.py` keeps (`/home/…/build/include/generated/constants/species.h`).
  The `gen_constants` edge that writes the header names it by relative path (`build/include/generated/constants/species.h`).
  ninja treats them as two files.
- So in the run that regenerates `species.h`, ninja doesn't know its dependents are dirty. They rebuild on the next run,
  once the header on disk is newer than the objects.
- The ROM target has no matching checks, so a single run builds a ROM without error, mixing objects compiled for
  the old and new constants. **Verified**: switching from the stock list to the test content, the first run compiled
  1 file and the second 197.

Every change that renumbers constants compiled code uses hits this: a species, an item, a sound, a text line. E1–E4a
appended or edited without renumbering what code uses, and their `--define` changes recompile everything anyway
(**Assumption** that their ROMs are unaffected). Fix: make `fix_depfile.py` write paths relative to the checkout, a
one-line change to offer upstream. Until then, a build runs ninja until nothing is left to compile (R-28).

## 7. Capacity

**Verified** in headers and packers at the pin:

| Limit | Value | Species it allows |
| --- | --- | --- |
| Pokédex save bitfields (`POKEDEX_SPECIES_BYTES` 0x54: the caught list and a seen list per sex and shininess) | 672 bits | 672 national species. Past that, the Pokédex save block grows, which needs a save layout change (E9, E6b) |
| Pokédex save `lastSpecies`; packed icon species (`POKEICON_PACK_SPECIES_MASK`); Pokédex size-order entries; Join Avenue species | 10 bits | 1023 |
| Encounter species, Entree Forest, Battle Subway | 11 bits | 2047 |
| Cry wave archives and banks | slots 1–999 (the next constant is fixed at 1000) | species + cry forms ≤ 999 |
| Pokédex other-language text | 493 (`POKEDEX_LANGUAGE_SPECIES_MAX`) | no effect past 493 |

The regional Pokédex has no length constant: `PML_PersonalLoadRegionalDexTable` counts the species that have a
regional number (`poke_personal.c`). A Kanto Pokédex of 151 is therefore data. **Verified** for that function; other
regional-Pokédex code (completion checks, ratings) wasn't audited.

## 8. Left alone, and known gaps

**Left at 649 on purpose**, because they check data to or from an unmodified game or a server: `cygnus_flow.c` (Global
Link), `mystery_gift_data.h`, `battle_rec.c`, `game_beacon_accessor.c` (4), `fest_mission_beacon.c` (2),
`gsync_state.c`, `gsync_disp.c`, `worldtrade_deposit.c` (GTS). These refuse #650, which is the safe answer. They are
Wi-Fi, C-Gear and Entralink features, switched per game (Q7).

**Known gaps** (code read; the effects are **Assumption** until seen in game):

| Gap | Effect | Fix |
| --- | --- | --- |
| Box Search (`box_search.c`) and the GTS (`worldtrade_deposit.c`) read the Pokédex's alphabetical list but hard-code where each letter starts and ends | From the inserted species' letter on, every letter's range is one entry early, and the last species falls off | Generate the boundaries from `orders.json`, or put added species at the list's end |
| Easy-chat words are numbered across categories, species first, up to the bad egg (`pms_words.py`) | An added species renumbers every later word. The build's constants follow; any data that stores word numbers as plain numbers wouldn't (**Unverified** whether any does) | Audit word numbers in data, or number added species' words last |
| The easy-chat input counts 649 species words (`pms_input_data.c`) | #650 can't be typed in easy chat | Derive the count; add the word to the input lists |
| Forms | E5's species has none. A species with forms needs form sprite groups, form records and Pokédex form bits (`POKEDEX_FORM_BYTES`) | Not tested |
| `day_care.c` keeps the original `>=` | The last national species can't inherit TMs from its father: #650 here, Genesect in Black 2 | Change to `>` behind a `KALEIDO_` define if it matters |

## 9. Cost

- **Once**: the patch (§2, §3), about 40 numbers and one packer helper. Upstream-friendly: it changes nothing for
  Black 2 and White 2 (Q10).
- **Per species**: a `species.txt` line; `res/pokemon/<species>/` (data, Pokédex data, 35 files when copied from a
  template); two sound list lines and a bank directory; seven Pokédex order entries; one `sPokeIconPalettes` byte.
  Phase 1's validator can check all of them.
- **Not needed for Tier 1**: Kanto's 151 and FRLG's 386 are within 649. This matters for Tier 2 and 3 (R-14).

## Not done

- In-game check: catch Kaleidomon on Route 19, see it in the Pokédex (list, entry, search), hear its cry, put it in a
  box and the party, save and reload. Deferred to the playtest pass (`docs/status.md`).
- New sprite art for an added species (§3), and a species with forms.
- The gaps in §8.
- The `fix_depfile.py` fix (§6) isn't offered upstream yet; that's a public pull request, sent when the owner says so.
