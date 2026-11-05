# pokebw2: the engine foundation

Research note for the Kaleido planning pass. Checked on 2026-11-03 against
[fuddlesworth/pokebw2](https://github.com/fuddlesworth/pokebw2) at commit
`41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c` (committed 2026-10-31, the head of `main` on the check date). Paths below are
relative to that commit unless a URL is given.

Tags: **Verified** (read in the source named), **Unverified** (not confirmed), **Assumption** (our inference, to be
tested).

## Identity and activity

- **Verified** (GitHub API): public, not a fork, not archived, GPL-3.0 (`LICENSE`), created 2026-10-04, last push
  2026-10-31. Repository size reported as ~339 MB.
- **Verified** (`README.md`): "A work-in-progress decompilation of Pokémon Black 2 and White 2, with a long-term goal of
  a native PC port." Both USA/Europe ROMs rebuild byte for byte from one source tree. The README's license line covers
  "the symbol names imported from swan" ([ds-pokemon-hacking/swan](https://github.com/ds-pokemon-hacking/swan), which
  `include/field/encounter.h` cites as GPL-3.0).
- **Verified** (git history): 4,179 commits in total. From 2026-10-15 to 2026-10-31, between 13 and 236 commits per day
  (median 105). Commit authors since 2026-10-01 include at least eight names (top four: 1,344, 898, 690 and 545
  commits). Non-merge commits since 2026-10-01 carry about 2,600 co-author trailers naming Claude or Codex.
  - Correction to the brief: activity is "hundreds per day" only on peak days, and the work is spread over several
    contributors, not one maintainer. Whether two of the top author names are the same person is **Unverified**.
- **Verified** (`CLAUDE.md`, `AGENTS.md`, `.claude/`, `.agents/`, `.codex/`): ships agent rules, skills, specialist
  agents, review agents and hooks; CI checks that the Claude and Codex copies stay in sync. A model for our own agent
  setup later, not something to copy now.

## Build

- **Verified** (`README.md`, `docs/building.md`): requires Linux, WSL or macOS, Python 3.11+, ninja, LLVM (`clang` and
  `llvm-objcopy` on `PATH`; they assemble the script archives). `python3 configure.py && ninja`.
- **Verified** (`docs/building.md`, `configure.py`): `configure.py` downloads pinned tools:
  wibo `pokebw2-sjis-1` (fork of wibo, SHA256-checked), sjiswrap `v1.2.2-pokebw2.1` (SHA256-checked), objdiff
  `v3.8.1`, dsd `v0.12.1-dsi.10` (from `fuddlesworth/ds-decomp`, a `dsi-hybrid` fork), and the Metrowerks compilers from
  `https://decomp.aetias.com/files/mwccarm.zip`. The Metrowerks tools are Windows programs run through wibo.
  - **Verified** (E0, `configure.py` lines 594–611 and `get_dsd`): `mwccarm.zip`, objdiff and dsd are downloaded
    **without** a hash check; wibo and sjiswrap are checked. The compilers are a proprietary toolchain on a third-party host: a
    reproducibility risk (R-12). Hashes recorded in `e0-baseline.md`.
- **Verified** (`README.md`): the build **requires the user's base ROM** in `orig/` (`baserom_b2_us.nds`,
  `baserom_w2_us.nds`). `ninja` extracts and delinks each ROM, compiles, links with `mwldarm`, rebuilds the ROM and
  checks the SHA1:

  | ROM (USA/Europe, NDSi Enhanced) | Input | SHA1 |
  | --- | --- | --- |
  | Black 2 | `orig/baserom_b2_us.nds` | `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb` |
  | White 2 | `orig/baserom_w2_us.nds` | `b5d7490be7b415b8f1e672a53e978a9cc667e56a` |

- **Verified** (`docs/building.md`): modified builds are `--bugfix` (enables `#ifdef BUGFIX` fixes, only in files marked
  complete) and `--shift 0x100` (pads code to test size changes). Both skip matching checks.
- **Verified** (`tools/decomp/compile_all.py` docstring, `.github/workflows/compile.yml`): `compile_all.py` compiles every
  C file for both versions **without a base ROM** (ROM blobs become zeros). Upstream CI runs it on every push and pull
  request.
- **Verified** (`.github/workflows/build.yml`): upstream's full ROM build in CI checks out ROMs from a private repository
  through a deploy key. Kaleido must not do this (brief, Section 6).
- **Verified** (`.github/workflows/standards.yml`): clang-format 23.1.1, `tools/decomp/check_style.py`, skills sync,
  nonmatching rows. Actions are pinned by tag (`@v7`), not SHA.

## Completeness

- **Verified** (`docs/nonmatching-functions.md`): "Every function is in C and matches, or is an asm function", with one
  game-code exception: `src/gfl/arc_tool.c`'s `ArchiveMoveImageTop`. Libraries (`lib/`) have documented SDK `asm`
  functions as well (`CLAUDE.md`, Rules).
- **Verified** (`docs/configs.md`, "Known gaps"): "dsd's analysis and linking have no known gaps left in this ROM."
- **Verified** (`config/b2_us/`): dsd configs exist for ARM9 only (main, ITCM, DTCM, two autoloads, the DSi LTD
  autoload, 344 overlay directories). There is no ARM7 config, and the docs never describe ARM7 code. ARM7 and ARM7i
  are taken unchanged from the base ROM (`tools/build/verify_dsi_rom.py` only hashes them).
  - **Assumption**: Tier 1 needs no ARM7 changes (sound driver, Wi-Fi, touch, RTC stay as shipped).
- ByteMatch figures: see `docs/research/hardware-and-rom.md`.

## DSi hybrid handling

- **Verified** (`docs/configs.md`, "DSi specifics"): Black 2 is an NDS/DSi hybrid built with TwlSDK. The build
  decrypts and re-encrypts ARM9i's modcrypt area, and **recomputes** every 0x400-byte sector's SHA1-HMAC digest and the
  header's per-program HMACs. The ARM9 secure area's digests are reused from the original "as long as the secure area
  is unchanged" (no ARM7 BIOS needed). The DSi-only LTD module is linked, recompressed and reinserted.
- **Verified** (`docs/code-organization.md`): overlay digests (`SDK_OVERLAY_DIGEST`) are filled by `dsd rom build`, so
  "a mod that changes an overlay gets its digest".
- **Unverified**: whether the header's RSA signature matters for the boot paths Kaleido targets. Nothing in the docs
  re-signs it (it cannot be re-signed without Nintendo's key). See `docs/research/hardware-and-rom.md` and experiment
  E7.

## Shift safety (code-size changes)

- **Verified** (`docs/configs.md`, "Shifting"): all pointer-like words that point at a symbol "have all been judged": six
  were real pointers and got relocations; the rest are constants or tables. `tools/decomp/unrelocated_pointers.py`
  lists candidates; `--shift` tests a padded build "by playing them".
- **Assumption**: code-size changes in any module are safe in principle; E3 confirms on a real battle change.

## Game data in `res/`

- **Verified** (tree count): `res/` holds 139,732 files. Upstream commits them. These are the B2W2 assets (provenance
  category 1); Kaleido never re-commits them.
- **Verified** (`docs/data.md`): archives built from source are packed from `res/` and checked against the original.
  Archives not built from source are linked in from the extracted ROM (`tools/build/files_tree.py`). Every archive's
  script "wrote its sources from the original … and can write them again".
  - **Assumption**: `res/` could be regenerated from a user's ROM if upstream stopped hosting it. Not tested; listed as
    a resilience experiment.
- **Verified** (`docs/data.md`) source kinds:
  - JSON per entity with a JSON Schema beside it, validated at pack time with "the file and field of any mistake".
    Files are ordered by the constant lists in `generated/`, so "adding an entry is adding its constant and its file".
  - Assembly for field scripts (`res/field/scripts/`) and trainer AI (`res/trainers/ai/`), via the C preprocessor and
    the same constants.
  - glTF 2.0 (`.glb`) for map models and field props; PNG for map/prop textures.
  - Indexed PNG + JASC palette + WAV for Pokémon and trainer sprites and cries.
  - Text: `res/text/{system,script}/*.txt`, one `ID = text` line per message; species/move/item/trainer text lives in
    their JSON and is pulled in by `\from{...}` lines.
- **Verified** (`docs/data.md`): version differences inside one file are written as `{ "black2": …, "white2": … }`
  (encounters, Pokédex areas, town map descriptions). A precedent for small per-version overrides.
- **Verified** (`generated/*.txt`, `res/` tree): 615 zone headers (`zones.txt`), 1,065 map models
  (`map_models.txt`), 409 map texture sets, 814 trainer constants (including `TRAINER_NONE`), 188 front trainer
  sprites, 385 field actor directories, and 685 species constants (`SPECIES_NONE`, 649 national species, Egg, Bad Egg
  and 33 Pokéstar pseudo-species).

### What the data formats can and cannot do today

| Content | Add new entries? | Evidence |
| --- | --- | --- |
| Species, moves, items, trainers, encounter tables, zones, trades | Yes: constant + file | `docs/data.md` (each section's "To add …") |
| Trainer sprites, field actors (overworld sprites) | Yes: constant + directory, copied from an existing one | `docs/data.md`, "Trainer sprites", "Field actors" |
| Zone events (NPCs, warps, signs, triggers) | Yes: JSON per zone | `docs/data.md`, "Zone events" |
| Field scripts, trainer AI | Yes: assembly source | `docs/scripts.md` |
| Text | Yes: lines in bank files | `docs/data.md`, "Text" |
| **Map models** | **No**: only the 1,065 existing models can be edited | `tools/data/map_model_data.py` `pack()` patches each model over `archive[chunk_id]` of the extracted original |
| **Map texture sets** | **No**: count must equal the original's 409 | `tools/data/map_texture_data.py` `pack()` raises "has N texture sets and its list M" |
| Map model materials / draw calls | No: "Adding material slots or draw calls is not yet supported" | `docs/data.md`, "Map model sources" |
| Map textures | Edit pixels only: "PNGs must … retain their dimensions"; palette capacity fixed | `docs/data.md`, "Map model sources" |
| Map geometry | Yes within a model: triangles are re-encoded when topology changes; terrain grid size fixed per chunk | `docs/data.md`, "Map model sources" |

This is the most important limit found. Gen 5-style Kanto needs hundreds of new map chunks and new texture sets, and
upstream's packers can only **edit** the original ones. See risk R-01 and experiment E4b.

## Battle code (overlay 167)

- **Verified** (`src/ov167/btl_calc.c`): crit chance is a stage table `CRITICAL_HIT_CHANCES[5] = { 16, 8, 4, 3, 2 }`
  rolled as 1 in N (`BtlCalc_RollCritical`). The type chart is a `const u8 TYPE_CHART[17][17]` (halves: 0, 2, 4, 8).
  Base damage is `power * attack * (level * 2 / 5 + 2) / defense / 50 + 2` (`CalcBaseDamage`).
- **Verified** (`docs/data.md`, "Moves"): each move has a `category` (`MOVE_CATEGORY_PHYSICAL/SPECIAL/…`) in its JSON.
  The physical/special split is per move, as data.
- **Verified** (`src/ov036/enc_pokeset.c`, `include/field/encounter.h`): seven encounter kinds (grass, dark grass,
  shaking grass, surf, rippling surf, fishing, rippling fishing). Grass slot odds are `20,20,10,10,10,10,5,5,4,4,1,1`;
  surf `60,30,5,4,1`; fishing `40,40,15,4,1` (first rows; other rows are Pass Power variants). The encounter rate climbs
  per step by a config (`EncountRateConfig`).

## Save data

- **Verified** (`src/gfl/savedata.c`, `src/gfl/backup_system.c`): the save is a table of blocks; total size is asserted
  against the save area size (`SaveDataSize … SaveAreaSize`). Actual sizes and free space are **Unverified** (E6).
- **Verified** (`docs/data.md`, "Constant lists"): event flags and variables have fixed ranges set by the event work
  code (saved flags from 1, trainer flags from 0x5f0, arrival flags from 0x9a5, daily flags 0xaa0–0xb03, hidden items
  from 0xb04, 64 temporary flags from 0x4000; variables 0x4000–0x41ae).

## Reusable B2W2 art for Kanto (category 1)

- **Verified** (`res/trainers/sprites/front/`): Gen 5 battle sprites already exist for `red`, `blue`, `giovanni`,
  `lance`, `brock`, `misty`, `lt_surge`, `erika`, `janine`, `sabrina`, `blaine`, and for many generic classes
  (`youngster`, `lass`, `hiker`, `fisherman`, `swimmer_m/f`, `biker`, `gentleman`, `psychic_m/f`, `black_belt`,
  `beauty`, `scientist_*`, `ace_trainer_m/f`, …).
- **Verified** (`docs/data.md`, "Species"): all 649 species, including every Gen 1–3 species, have Gen 5 animated
  battle sprites, icons and cries in `res/pokemon/`.

## Engine conventions to follow

- **Verified** (`CLAUDE.md`, `docs/code-organization.md`): one source file per original file; English names; natural C
  only; bugs as `// BUG:` plus `#ifdef BUGFIX`. clang-format 23.1.1 with `.clang-format`; `check_style.py`.
- **Verified** (`CLAUDE.md`): other decomps (pret) are references only, "never paste their code". Kaleido adopts the
  same rule.
- **Verified** (`CLAUDE.md`, "Publish every commit"): upstream pushes straight to `main` after a matching build. Not
  our workflow; noted so agents don't copy it.

## Field script semantics (Phase 3, step 3)

Read in the code at the pin, 2026-11-05, for writing story scripts:
- **`VMJumpIf CMP_STACK` jumps when the comparison on the stack is false.** It jumps when the popped value isn't 1
  (`Scrcmd_Vm_VMJumpIf`, `src/ov012/scrcmd_vm.c`). `docs/scripts.md` says it jumps when the result is true, but Black
  2's scripts use it the code's way. Kaleido's scripts wrap it in named macros (`frlg_story.inc`). **Verified**.
- **`YesNoWin` stores 0 for yes and 1 for no** (`src/ov036/scrcmd_menu.c`). **Verified**.
- **An NPC appears only while its spawn flag is clear** (`SpawnAllZoneNPCs`, `src/ov012/field_actor.c`). **Verified**.
- **A zone's map script table** (`init_<zone>.s`, mirrored in its events' `init_scripts`):
  - type 2 runs a script as the zone loads;
  - type 1 runs one of its conditions' scripts when the condition's variable has its value, as Black 2's scenes do.

  **Verified** from Black 2's own tables and scripts; the code that reads the table isn't named yet.
- **Black 2's first rival battle** is `CallTrainerBattle` with 1 as its third argument, then `CallTrainerBattleEnd`;
  a loss carries on without a blackout (`aspertia_city.s`). **Verified** from the script; in game, **Unverified**.

## Not yet checked

- `docs/porting-notes.md`, `docs/matching.md` (474 KB) and `docs/source-files.md` were skimmed only for the facts above.
- Whether `configure.py` can take extra preprocessor defines beyond `--bugfix` (needed for rulesets). **Unverified**;
  assumed to need a small engine patch.
