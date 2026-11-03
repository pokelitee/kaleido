# Peripheral tools and reference decompilations

Research note for the Kaleido planning pass, checked on 2026-11-03 through the GitHub API, shallow clones of wikis,
and the files named below. Tags: **Verified** (read in the source named, at the commit given), **Unverified**,
**Assumption**.

Licenses were checked twice: GitHub's license API and a listing of the repository root (GitHub's detection can miss a
license file that isn't at the root). The license checks for CTRMap-CE, CTRMapV, White2Upgrade and swan, and
White2Upgrade's Pokédex save struct, were repeated independently after the first survey.

## Summary

| Repository | License | HEAD (12) | HEAD date | Stance | Reason |
| --- | --- | --- | --- | --- | --- |
| fuddlesworth/pokebw2 | GPL-3.0 | `41f42ca1afe6` | 2026-10-31 | **use** (engine) | See `pokebw2.md` |
| ds-pokemon-hacking/White2Upgrade | **none** | `882df3f92d00` | 2025-05-05 | research only | No license; commits game-derived binaries; best record of expansion limits |
| PlatinumMaster/SwissArmyKnife | **none** | `08c997485826` | 2023-05-22 | exclude | Dormant, no license, binary ROM editor |
| FrostFalcon/FrostsGen5Editor | **none** | `572e4c2e242d` | 2026-10-27 | exclude (at most inspect built ROMs) | No license, ROM-only Windows editor |
| ds-pokemon-hacking/CTRMap-CE | GPL-3.0 | `74e2b035ac73` | 2026-04-16 | research only | Works on ROMs or extracted files, no glTF |
| ds-pokemon-hacking/CTRMapV | **none** | `3c2778095867` | 2026-04-16 | research only | All of CTRMap's Gen 5 support is here, unlicensed |
| ds-pokemon-hacking/PMC | GPL-3.0 | `c65ebc12d3c4` | 2026-03-01 | exclude | ROM code injection; redundant on a decomp |
| ds-pokemon-hacking/swan | GPL-3.0 | `4324f73a7659` | 2025-07-03 | reference | B2W2 symbols and headers; pokebw2 imports its names |
| pret/pokered | **none** | `0dbf95cd12f5` | 2026-10-31 | reference only | Behavior and formats; never copy |
| pret/pokeyellow | **none** | `b452f2ab0718` | 2026-11-01 | reference only | as above |
| pret/pokecrystal | **none** | `3c813b0b4d82` | 2026-10-30 | reference only | as above |
| pret/pokefirered | **none** | `ce6406d8c2ea` | 2026-10-20 | reference only | as above |
| pret/pokeemerald | **none** | `731ad5bfd6e6` | 2026-10-01 | reference only | as above |
| pret/pokediamond | **none** | `b623abef1b4d` | 2026-10-11 | reference only | as above |
| pret/pokeplatinum | **none** | `c6689696d5fb` | 2026-11-01 | reference only | as above |
| pret/pokeheartgold | **none** | `e1d5a4606640` | 2026-11-01 | reference only | as above |
| jmacd/xdelta | Apache-2.0 (`xdelta3/LICENSE`) | `5d936d2c30f7` | 2026-10-13 | **use** | Patch format the brief requires |
| RoadrunnerWMC/ndspy | GPL-3.0 | `00165f177d03` | 2026-08-29 | candidate | Python DS formats library, if we need NARC/NDS reading outside upstream's tools |
| Garhoogin/NitroPaint | BSD-2-Clause | `1e24113daf50` | 2026-10-29 | dev tool | Nitro 2D/texture editor for artists |
| devkitPro/ndstool | GPL-3.0 (`COPYING`) | `76e8b681bb22` | 2024-01-08 | not needed | upstream's dsd already packs ROMs |

## White2Upgrade: how dex expansion and Fairy were done (research only)

Repository facts (**Verified**): default branch `main` (HEAD `882df3f9…`, 2025-05-05); a `dev` branch (HEAD
`fd99f371…`, 2026-06-04) moves the build to Meson, TOML and a CTRMap project. No license in either branch. It commits
`pmc/ARM9PMC.bin` (a pre-patched ARM9 that replaces the game's) and a 512 KiB save on `main`. The build needs a US
White 2 ROM, unpacks it with ndstool and links patches as a DLL through CTRMap's RPMTool (wiki `Setup.md`, `Makefile`).
It is ROM patching, not a source build.

Limits and pitfalls it hit, all **Verified** at `main@882df3f9` with the file named. We record ideas and numbers only;
no code is copied.

| Area | Finding | Source |
| --- | --- | --- |
| Species cap | 721 species, regional dex 302; constant caps patched in an ARM9 routine and Pokédex overlays 299 and 302 (`721`, `2*721`) | `src/Expansion_LimitAdjust.s` |
| IDs past 649 | Vanilla treats IDs just past 649 as egg slots; the personal-data loader had a limiter for indexes 650 and 651 that had to go | commit `9489faa18a`, `PML_PersonalGetDatID` patch |
| Personal data `a/0/1/6` | 0x4C-byte records; vanilla 710 records; expanded to 826; regional dex table stored as file 826 | `dev:docs/narc-structures.md`, `data/pml/personal/` |
| Abilities | Ability 1, 2 and hidden are **u8** in personal data: 255 abilities max without a format change | `include/Personal.h` |
| Evolutions `a/0/1/9` | 7 → 8 slots of 6 bytes; the reader's size and loop had to change | `CheckEvolveSpecies` patch, PR #3 |
| Encounter slots `a/1/2/7` | Species is 11 bits (max 2047), form 5 bits; record 0xE8; grass 12 slots, surf and fishing 5 | `dev:docs/narc-structures.md` (pokebw2's `include/field/encounter.h` agrees) |
| **Save: Pokédex** | Seen/shiny-by-sex bitfields are 84 bytes each = **672 species**; 721 needs 91. The save layout was **not** grown: "the save file has not been extended and the PokéDex flags get all messed up" | `src/w2u_pokedex.cpp` lines 22–25, 286 |
| Save: forms | Form bitfields 11 bytes (88 bits); form list capped at 72 entries | `src/w2u_pokedex.cpp`, `data/poke_form_list.bin` |
| Battle sprites `a/0/0/4` | 20 files per species at `20 × dex number`; forms moved to the end of the archive | `src/w2u_pokegra.cpp`, wiki `Contribution-Guide.md` |
| Icons `a/0/0/7` | Indexed `2 × species + 8`; forms from 1456; icon palettes need a new lookup table | `src/w2u_pokegra.cpp` |
| Footprints `a/1/6/5` | A missing footprint for a new species crashed the catch screen | commit `c7d12755a3` |
| Heap | Pokédex process heap raised to `0x1B00` (original **Unverified**) | `Pokedex_CreateProc` patch |
| Fairy type | 17 → 18 types; 17 was the "no type" sentinel, so every hard-coded 17 had to move (Conversion, Conversion 2, Color Change, Transform/Imposter, battle overlays 167/168, several UI loops); type chart becomes an 18×18 table | `include/Types.h`, `src/Fairy_LimitAdjust.s`, PR #2 |
| Fairy bugs | Battle crash from a missing Fairy move-button graphic (issue #6); Hall of Fame effect still borrowed from Normal | issues, `src/Types.cpp` |
| Build | Incremental builds broken, "extremely slow" (open issue #4) | issue #4 |

What this means for Kaleido:

- Species past 649 touch save layout (Pokédex bitfields hold 672 at most), several archives indexed by species ×
  constant, sentinel values, and at least two overlays. That supports the brief's call to treat expansion as its own
  experiment (E5), not a Tier 1 requirement.
- Fairy is mostly a hunt for hard-coded `17`s. A decomp makes that search tractable (grep the C and constants instead
  of disassembly).

## CTRMap-CE and CTRMapV

- **Verified**: CTRMap-CE is GPL-3.0 with a non-binding request ("CFRU clause") not to monetize games made with it.
  23 commits from 2026-01-26 to 2026-04-16; pre-releases through 2026-04-28.
- **Verified**: the Gen 5 support lives in the separate CTRMapV plug-in, which has **no license**. Its features: zone
  editor, warps/NPCs/triggers/events, props and buildings, cameras and rails, a scripting assistant, Gen 5 format
  readers (area, buildings, camera, map matrix, map replacement, NPC registry, rail, terrain, zone), and code-injection
  tools (PMC, RPM).
- **Verified**: CTRMapV reads and writes NSBMD, NSBTX, NSBCA, NSBTA and NSBVA. CTRMap-CE's CreativeStudio imports and
  exports COLLADA, OBJ, SMD and its own CMIF; **no glTF** (code search on default branches finds none).
- **Verified** (docs site `bw_b2w2-using_ctrmap.md`, docs repo `f5f5f80d`, 2026-10-24): it works from a ROM or an
  extracted game directory (IRAO, IRBO, IRDO, IREO), as a Java GUI project.
- **Assumption**: CTRMapV can create **new** NSBMD map models from imported meshes, which pokebw2's packers cannot do
  yet (R-01). Even so, it is unlicensed and works on extracted ROM files, so it can't be part of our pipeline. At most
  an artist could use it locally to inspect or prototype, and its file-format behavior (not code) could inform our own
  encoder. **Unverified** whether its model import produces Gen 5-valid map chunks.

## pret decompilations

- **Verified**: none of the eight has a license file; the license API returns 404 for each. They stay references for
  behavior and data formats. We never copy code, data files or labels from them.
- **Verified** (`pokefirered@ce6406d8`, `*.sha1` files and README): ROM SHA1s

  | ROM | SHA1 |
  | --- | --- |
  | FireRed (USA, rev 0) | `41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc` |
  | FireRed (USA, rev 1) | `dd5945db9b930750cb39d00c84da8571feebf417` |
  | LeafGreen (USA, rev 0) | `574fa542ffebb14be69902d1d36f1ec0a4afd71e` |
  | LeafGreen (USA, rev 1) | `7862c67bdecbe21d1d69ce082ce34327e1c6ed5e` |

  The README also lists "switch" builds (`baa452d0…`, `62b9fc77…`), which are not targets.
- **Verified**: pokefirered builds without a base ROM (no `baserom` in the `Makefile`; assets committed).
- **Verified** (`src/data/wild_encounters.json`): FRLG wild encounters are JSON grouped by map with land (12 slots),
  water (5), rock smash (5) and fishing (10: Old Rod 2, Good Rod 3, Super Rod 5) groups. Slot odds: land
  `20,20,10,10,10,10,5,5,4,4,1,1`, water and rock smash `60,30,5,4,1`, fishing `70,30 | 60,20,20 | 40,40,15,4,1`. 264
  encounter entries, half suffixed `_FireRed` and half `_LeafGreen`.
- **Verified** (`pokefirered/src/battle_script_commands.c`): crit chance table `{16, 8, 4, 3, 2}`, the same as
  pokebw2's `CRITICAL_HIT_CHANCES`.
- **Verified** (tree of `pokefirered@ce6406d8`): 425 maps, 367 layouts, 2 primary and 66 secondary tilesets, 146
  trainer front pictures, 96 overworld "people" sprites. 147 maps belong to the Sevii Islands, Navel Rock, Birth Island
  and Trainer Tower groups.

## Other licensed tooling

- **Verified**: xdelta3 is Apache-2.0 (license in `xdelta3/LICENSE`, so GitHub's detector misses it), HEAD
  `5d936d2c30f7` on 2026-10-13. Determinism of its output: see `hardware-and-rom.md`.
- **Verified**: ndspy (GPL-3.0, active 2026-08-29) and NitroPaint (BSD-2-Clause, active 2026-10-29) are compatible
  with our licensing if we ever need them. Neither is a dependency yet.
