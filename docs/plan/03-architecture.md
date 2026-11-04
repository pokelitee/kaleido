# 03 — Architecture

Status: **proposal** for owner review (planning pass, 2026-11-03). Nothing here is built yet. Facts about pokebw2 come
from `docs/research/pokebw2.md` (commit `41f42ca`). Where a design choice rests on an untested assumption, the
experiment that tests it is named (E-numbers are defined in `05-roadmap.md`).

## 1. Principles

1. **Upstream does the heavy lifting.** pokebw2 already builds the ROM from source, packs `res/` from JSON, glTF, PNG
   and assembly, and validates against JSON Schemas. Kaleido adds layering, provenance, extraction and per-game
   configuration around it, and changes the engine only where a game needs it.
2. **No Nintendo bytes in anything we host.** Upstream B2W2 content reaches a build through the pinned engine. Other-game
   content is extracted on the builder's machine from their own ROMs. Our repo holds code, original content and
   manifests.
3. **Compile time over run time.** Game differences are preprocessor defines and data, not runtime switches.
4. **Gen 5 mechanics everywhere.** Every game plays by B2W2's rules (owner's decision, Q6); only content comes from the
   original game. This replaces the brief's generation rulesets.
5. **The matching build stays reproducible.** With every Kaleido flag off and no content layers, the patched engine
   must still rebuild Black 2 byte for byte. That is the regression baseline for every engine change and upstream sync.
6. **Smallest thing that works for Tier 1.** No plugin system, no runtime scripting layer, no Tier 3 abstractions.

## 2. Hierarchy

```
Engine     pokebw2 at a pinned commit + Kaleido's engine patch series (GPL-3.0)
  └ Framework   build tooling, layering, provenance, schemas, extractors (GPL-3.0)
      └ Region      shared geography: location IDs, place names, town map, map art shared by every game set there
          └ Family     a set of games with one story: maps, NPCs, events, scripts, progression (FRLG, RBY)
              └ Game      one ROM: version exclusives, title, save identity, B2W2-system switches (FireRed, LeafGreen)
```

- Region `kanto` holds what FRLG and RBY share. RBY's family overrides where Gen 1 Kanto differs from FRLG's. A later
  GSC/HGSS family can override more of the same region without changing it (Tier 2 is not blocked).
- Version pairs (FireRed/LeafGreen, Red/Blue, later Yellow) are games under one family. Their layers should be small:
  exclusives, title screen, a few scripts.

## 3. Repository layout

```
kaleido/
├── AGENTS.md, CLAUDE.md, README.md, CONTRIBUTING.md, LICENSE, LICENSE-CONTENT
├── engine/
│   ├── pokebw2/              git submodule → github.com/fuddlesworth/pokebw2 at the pinned commit (pointer only)
│   ├── patches/              Kaleido's engine changes, NNNN-topic.patch, applied in order
│   └── engine.toml           upstream URL, optional mirror URL, notes on the pin
├── framework/
│   ├── kaleido/              Python package and CLI: doctor, bootstrap, extract, merge, validate, build, patch, test
│   ├── schemas/              Kaleido's schemas (game, layer, provenance) and extensions of upstream's
│   ├── extractors/           readers for source-game formats (GBA Gen 3, GB Gen 1): code only, no game data
│   └── tests/                host-side unit tests with synthetic fixtures
├── content/
│   ├── regions/kanto/        a layer (see §5)
│   ├── families/frlg/        a layer
│   └── games/{firered,leafgreen}/   a layer + game.json
├── docs/                     source of truth (architecture, ADRs, research, plan, status, risks)
└── (ignored) orig/  build/  extract/  dist/  .cache/  .venv/
```

Phase 1 creates this skeleton. Only `docs/` and the repo records exist after the planning pass.

## 4. Engine integration

Accepted in `docs/decisions/0002-engine-integration.md`: a git submodule pointing at **upstream** pokebw2 (not a fork),
pinned to one commit, plus an ordered **patch series** in `engine/patches/`. The submodule records only a commit ID, so
our repository holds no Nintendo assets. A GitHub fork would be public by GitHub's rules, and a private mirror would
put ~140k extracted assets under the owner's account.

How it works:

- `kaleido bootstrap` checks out the submodule at the pin, creates a local branch, and applies the series with
  `git am`. Developers change the engine on that branch and export it back with `kaleido engine export` (a
  deterministic `git format-patch`), so the series in our repo is always the source of truth.
- Every behavior change in a patch is behind a preprocessor define (`KALEIDO_*`). The first patch teaches
  `configure.py` to take Kaleido's defines and content overlay (upstream only knows `--bugfix` and `--shift`).
- Changes upstream would want (new-entry support in packers, a generic `--define`) are offered upstream first, which
  shrinks our series.
- Upstream sync is deliberate: pick a commit, re-apply the series, rebuild the matching baseline, run our tests and
  every game build, then bump the pointer and series in one commit. The procedure becomes `docs/engine-sync.md` in
  Phase 1.

## 5. Content layers

A layer is a directory shaped like upstream's tree, plus two manifests:

```
content/families/frlg/
├── layer.json          name, kind (region | family | game), parent layer, extraction recipes it owns
├── provenance.json     every committed path → exactly one category (see §6)
├── generated/          constant-list additions (new ZONE_*, TRAINER_*, ITEM_* …), append-only
├── res/                files at upstream's paths: res/field/events/<zone>.json, res/trainers/data/<t>.json …
└── extract/            extraction recipes: which source ROM table becomes which res/ file (no game data)
```

### Merge rules

For game G, the merged tree is: upstream `res/` and `generated/` → region → family → game. Within a layer, committed
files and that layer's extracted files are merged together. A path that both provide is an error.

| Layer file | Effect on the merged tree |
| --- | --- |
| `res/P` | Replaces `P` from lower layers (whole file). |
| `res/P.merge.json` | Applied to the lower `P` as an RFC 7396 JSON Merge Patch. For small overrides, such as one encounter group or one learnset. Arrays are replaced whole. |
| `generated/<list>.txt` | Appends constants to upstream's list. Duplicates are an error. Upstream constants are never renamed or removed, because engine code refers to them. |

- Content that replaces B2W2 behavior repurposes existing IDs by overriding their files (the new game's start zone, its
  title screen), or adds new IDs. Tier 1 zones always reuse existing zone IDs, recorded in the region's mapping
  (ADR 0004). Unova content stays in the ROM, unreferenced, unless ROM space requires pruning
  (measured by E6).
- The merge writes into a per-game engine worktree (§7) and rewrites only files whose bytes changed, so ninja's
  incremental build still works.
- The merge also writes `build/<game>/merge-report.json`: every output path, the layer it came from and its provenance
  category. Validation and debugging read it.

### Why upstream's formats suffice

Upstream already has per-entity JSON with schemas, constant lists that set IDs, text banks with stable message IDs,
glTF maps, and assembly scripts. Kaleido needs only layering, merge patches and manifests on top. No parallel data
format is proposed. Upstream's limits are recorded in `docs/research/pokebw2.md`; the binding ones are that new map
models and texture sets can't be added yet (R-01, E4b).

## 6. Provenance

Each layer's `provenance.json` assigns every committed file to exactly one category. The build and CI validate it.

| Category | What | Where it lives | Rule enforced |
| --- | --- | --- | --- |
| 1 `upstream` | B2W2 data in pokebw2's `res/` | the engine submodule | never committed in our repo |
| 2 `extracted` | other-game content (FRLG text, parties, encounters, learnsets) | `build/<game>/extracted/` | must not exist in git. Only its recipe and an SHA1-gated source are committed |
| 3 `original` | our art, maps, scripts, data | layers, committed | `LICENSE-CONTENT` |
| 4 `third-party` | community assets | layers, committed | each entry names the license, author, source URL and what use it permits |

```json
{
  "$schema": "../../../framework/schemas/provenance.schema.json",
  "entries": [
    { "paths": ["res/field/scripts/kanto_*.s"], "category": "original" },
    { "paths": ["res/trainers/data/**"], "category": "extracted", "recipe": "extract/trainers.json" },
    { "paths": ["res/field/actors/npc_old_man/**"], "category": "third-party",
      "license": "CC-BY-4.0", "author": "…", "source": "https://…" }
  ]
}
```

- Extraction recipes reference source tables by ROM offset or pointer-table index for one pinned revision of the
  source ROM. A recipe holds locations and transforms, never the extracted bytes. E8's extractor finds FireRed's
  wild encounter tables by their structure and names maps by the ROM's own text, so its recipe needs no offsets
  (`docs/research/e8-extract-encounters.md`).
- **Assumption**: offset tables and IDs we assign are not other-game content. Distribution is decided in Q1: patches
  carry the extracted content they add.
- A guard (CI and a pre-commit hook in Phase 1) rejects ROM files and any path that a category 2 entry covers.

## 7. Build pipeline

All builds run in Linux or WSL2, because upstream needs them. Python is the only language Kaleido's tooling adds, and
upstream already uses it.

```
kaleido doctor            environment, tool versions, disk, base ROM and source ROM SHA1s, with actionable errors
kaleido bootstrap         submodule at pin → apply patches → venv → upstream tools (shared cache) → orig/ links
kaleido extract <game>    source ROMs (SHA1-checked) → build/<game>/extracted/  (category 2, deterministic)
kaleido merge <game>      layers + extracted → build/<game>/engine/{res,generated}  + provenance and schema checks
kaleido validate <game>   cross-references on the merged tree (warps, scripts, text IDs, encounters, trainers, IDs)
kaleido build <game>      upstream configure.py with the game's defines → ninja → build/<game>/kaleido-<game>.nds
kaleido patch <game>      xdelta3 against the base ROM → dist/<game>.xdelta + checksums for players
kaleido baseline          patched engine, every flag off, no layers → must equal Black 2's SHA1
```

- **Per-game engine worktree**: `build/<game>/engine/` is a `git worktree` of the patched engine. Each game keeps its
  own ninja state, and builds of two games don't invalidate each other. Upstream's worktree guidance (link `orig/`,
  `.venv` and the downloaded tools) applies. Cost: one checkout per game (`res/` alone is ~140k files).
- **Incremental**: a top-level `build.ninja` generated by `kaleido` runs extract → merge → engine ninja, with restat, so
  an unchanged layer rebuilds nothing. Upstream's depfiles miss regenerated constant headers within one ninja run
  (R-28, E5), so until `fix_depfile.py` is fixed, `build` runs the engine's ninja again until nothing is left to
  compile.
- **Deterministic**: pinned tool versions and hashes, sorted file walks, canonical JSON output, no timestamps or
  environment data in outputs. xdelta 3.2.x writes file names and BLAKE3 "armor" into the patch header by default, so
  patches are made with a pinned xdelta and `-a -A= -S none` plus a source window covering the 512 MB base ROM
  (**Assumption**, tested in Phase 1; `hardware-and-rom.md`). Phase 1's exit criterion checks it: a clean clone on a
  second machine builds the same ROM hash.
- **Working copy location**: build in WSL's own filesystem, not `/mnt/c`. **Assumption**: 9P file access makes a
  140k-file build much slower; measured in E0.
- **Tool cache**: upstream's downloaded tools (wibo, sjiswrap, objdiff, dsd, mwccarm) are cached once under
  `.cache/tools/` with recorded hashes. `doctor` checks them, because the Metrowerks package comes from a third-party
  host (R-12). dsd is the exception: until upstream takes Kaleido's change, bootstrap builds it with Rust from
  `ds-decomp` and `ds-rom` at pinned commits plus `--allow-stale-secure-area` (ADR 0004).

## 8. Configuration

### Game

```json
{
  "$schema": "../../../framework/schemas/game.schema.json",
  "id": "firered",
  "title": "Kaleido FireRed",
  "layers": ["regions/kanto", "families/frlg", "games/firered"],
  "engine": { "base_rom": "b2_us", "defines": { "KALEIDO_CGEAR": 0 } },
  "sources": [{ "id": "firered", "format": "gba", "sha1": ["<one pinned revision>"] }],
  "save": { "signature": "KLD-FR" },
  "outputs": { "rom": "kaleido-firered.nds", "patch": "kaleido-firered.xdelta" }
}
```

- Each game names exactly one source ROM revision at first (Q5). Supporting a second revision means a second offset
  table, not new code.
- The framework stays versionless while there is one game. Once a second game is release-bound, games pin a framework
  version and schemas get migrations (brief, Section 6).

### Mechanics

Every game uses Gen 5 mechanics, unchanged from B2W2 (owner's decision, Q6 and Q9). That replaces the brief's
generation rulesets (Sections 4 and 5): there is no ruleset file, data transform or mechanic variant.

- **Gen 5 decides how things work**: battle and field rules, move data (power, accuracy, PP, type, category), species
  stats, types and abilities, as `res/` has them.
- **The original game decides what is in it**: story, dialogue, maps, trainers and parties, wild encounters, items,
  learnsets and TM contents. These are extracted or authored per layer.
- Where an original game relies on something Gen 5 lacks (FRLG's Old and Good Rods, Rock Smash encounters, a field
  move B2W2 doesn't have), the content is adapted and the feasibility tables mark it Approximate.
- If a later game ever needs a different mechanic, the variant is added then: a `KALEIDO_*` define chosen in that game's
  `game.json`, the same way B2W2 systems are switched.

### B2W2 systems

Each B2W2-only system (C-Gear, Pass Powers, Entralink, Join Avenue, seasons, Hidden Grottoes, PWT, Medal Rally,
Pokéstar Studios, Memory Link, Unova Pokédex, Wi-Fi and infrared features) is a compile-time switch, and each game's
config picks (owner's decision, Q7). With a switch off, the system's code and data stay out of the build where the
engine allows, which recovers RAM and overlay space (R-05, R-15). Phase 1 inventories the systems and their entry
points; the first switches arrive with the Phase 3 prototype.

### Save identity

- Keep B2's header game code (`IREO`) and its 512 KB FLASH save. melonDS picks save type and ROM size by game code
  (**Verified**, `hardware-and-rom.md`); TWiLight Menu++ and nds-bootstrap key per-game handling on it too. E7 checks
  flashcarts on hardware.
- Each game has its own save magic, `KALEIDO_SAVE_MAGIC` in its game config. It replaces the save footers' magic and the
  outside data's, so another game's card, B2's included, reads as empty (E9, `docs/research/e9-save-identity.md`). The
  validator keeps each game's value unique and away from B2's two magics, 0 and 0xffffffff.
- Emulators and flashcarts already keep one save file per ROM file name.

## 9. Validation

- **Schemas**: upstream's JSON Schemas for every `res/` file. Kaleido extends them with `allOf` wrappers instead of
  editing them. Kaleido's own files (`game.json`, `layer.json`, `provenance.json`, recipes) have schemas.
- **Cross-references** on the merged tree, naming the file and field of each error: warps point to existing zones and
  warp indices; zone headers name existing scripts, text banks, encounter tables, matrices and areas; scripts use
  defined text IDs and flags; encounters, trainers and learnsets use species, moves and items that exist; trainer
  classes have sprites; NPC caches stay within 26 object codes per zone (upstream's documented limit).
- **Provenance**: every committed path is covered exactly once; category 2 paths are absent from git; category 4 has
  a license record.
- **ROM**: header and digests (`tools/build/verify_dsi_rom.py`); ROM ≤ 512 MB and ARM9 ≤ 2.5 MB
  (`hardware-and-rom.md`); overlay table sanity.
- **RAM (DS mode)**: `0x023e0000` minus the build's `OV290_BSS_END` must cover the fixed root heaps and the extra heap
  plus a margin (`docs/research/e6-headroom.md`), so overgrowth fails the build instead of the boot.

## 10. Distribution

- One xdelta patch per game, from the Black 2 base ROM. Release notes give the base ROM's SHA1
  (`e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`), the output's SHA1 and the patcher to use.
- **Decided (Q1)**: a patch carries the extracted FRLG content it adds; no player-side builder.
- **Open until the first release (Q1)**: the publishing channel. The brief bans ROM-derived data from GitHub, and
  patches are ROM-derived, so no GitHub Releases unless the owner changes that rule.
- **GPL-3.0**: distributing a patch distributes compiled GPL code; recipients must be able to get the corresponding
  source (R-07). The repository is public, so each release tags its exact source commit and links it.

## 11. Licensing boundaries

| Part | License |
| --- | --- |
| `engine/patches/`, `framework/` | GPL-3.0 (required: derived from GPL-3.0 pokebw2) |
| `content/` original files (category 3) | **CC BY-SA 4.0** (`LICENSE-CONTENT`; decided in Q8) |
| `content/` third-party files (category 4) | as recorded per entry |
| `docs/` | proposed CC BY-SA 4.0 with the content |

Why CC BY-SA 4.0: Creative Commons declared GPLv3 a "BY-SA–Compatible License" for 4.0 on 2015-10-08, one way only
(BY-SA material may be adapted under GPLv3, not the reverse). **Verified**:
[creativecommons.org compatible licenses](https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/),
fetched 2026-11-03. That lets our art ship inside GPL builds and other GPL projects, with attribution. Alternative:
CC BY-NC-SA 4.0 signals non-commercial intent but is not GPL-compatible, so it would bar reuse in GPL projects.

## 12. What stays out

- No ARM7 changes (`pokebw2.md`: ARM7 is passed through from the base ROM).
- No runtime scripting layer or plugin system: field scripts stay upstream's assembly.
- No Tier 3 structures: no generic "gimmick" framework, no species-expansion scaffolding. E5 measured what expansion
  costs (`docs/research/e5-species.md`); Tier 1 needs none.
- No pret code or data in the repo. pret is a reference for behavior and formats. A builder's local pret checkout may
  later be an optional extraction input (brief, Section 3), never a committed one.
