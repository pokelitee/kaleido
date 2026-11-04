# Architecture

The architecture as it exists now. The full design is in `docs/plan/03-architecture.md`; this file tracks what is
decided and what is built.

## Built

Phase 1 (`docs/plan/05-roadmap.md`) is building the skeleton. So far:

| Part | State |
| --- | --- |
| Repository layout (`03-architecture.md` §3) | `engine/`, `framework/` and `content/` exist with READMEs; their contents come next |
| Licenses | `LICENSE` (GNU GPL v3.0, the same text as pokebw2's) and `LICENSE-CONTENT` (CC BY-SA 4.0) |
| Framework | `./kaleido doctor`, `bootstrap`, `check`, `baseline`, `compile` and `build <game>` (`framework/kaleido/`, Python 3.11+, standard library only) with `unittest` tests in `framework/tests/`; `pyproject.toml` holds Ruff's settings. Games build in worktrees under `build/<game>/engine/`, sharing `engine/pokebw2/tools/` |
| CI | `.github/workflows/ci.yml`, no ROM anywhere: a Framework job (Ruff, unit tests, `kaleido check`) and an Engine job (series at the pin, clang-format on its C files, `kaleido compile`, `validate --no-extract`), joined in one `CI` check. Actions pinned by SHA, read-only permissions, timeouts. Dependabot: weekly, grouped, pip (Ruff) and actions |
| Layers | `extract` (recipes on SHA1-checked source ROMs into `build/<game>/extracted/`), `merge` (replace, JSON merge patch, message overrides, constant appends; provenance checked per file; a merge report) and `validate` (the layers' JSON against pokebw2's schemas, with its own checker; warps, encounter tables, species and levels, region zones). Kaleido's own files are checked by the code that reads them, not by JSON schemas. Extractors in `framework/extractors/`: Gen 3 wild encounters |
| Patches | `kaleido patch`: xdelta3 3.0.11 with `-e -9 -S none -A`, checked by applying it; `dist/kaleido-<game>.xdelta` and `.sha1`, never committed |
| Games | `firered`: title "Kaleido / FireRed", `KALEIDO_SAVE_MAGIC` `0x4b465231`, and test layers `regions/kanto` (`route_1` → `ZONE_ROUTE_19`), `families/frlg` (Route 1's encounters, extracted), `games/firered` (one original text line). `red`, a stub with no source ROM: title "Kaleido / Red", `KALEIDO_SAVE_MAGIC` `0x4b524431`, `KALEIDO_NO_CGEAR`, and layers `regions/kanto`, `families/rby` and `games/red` (one original text line each) |
| B2W2 systems | One compile-time switch so far, `KALEIDO_NO_CGEAR` (patch `0006`); a first inventory of the systems is `docs/research/b2w2-systems.md` |
| Contributor and build docs | `CONTRIBUTING.md`, `docs/building.md` (the manual procedure until `kaleido` exists), `docs/engine-sync.md` |
| Engine | `engine/pokebw2`, a submodule at the pin `41f42ca` (fetched with `--depth 1`); `engine/patches/` with six patches (`--define`, the dsd flags, `KALEIDO_SAVE_MAGIC`, `compile_all.py --define`, `--banner-title`, `KALEIDO_NO_CGEAR`); `engine/engine.toml`; Kaleido's dsd change in `engine/dsd/`. With every define off the patched engine matches Black 2 (verified 2026-11-04) |

## Decided

| Decision | Record |
| --- | --- |
| Architecture decisions are ADRs in `docs/decisions/` | ADR 0001 |
| pokebw2 is a git submodule pointing at upstream, pinned to one commit; Kaleido's engine changes are a patch series in `engine/patches/`, each behind a `KALEIDO_*` define; with every define off the engine rebuilds Black 2 byte for byte | ADR 0002 |
| New map art: map models and texture sets are appended from a template (upstream packers extended, offered upstream) through Phase 3; a glTF → Nitro encoder is built before Phase 4; each chunk must fit its map type's `chunkBufferSize` | ADR 0003 |
| Tier 1 Kanto zones reuse existing zone IDs. Builds that change ARM9 main use Kaleido's dsd flag `--allow-stale-secure-area`, or `--arm7-bios` when a builder has the BIOS | ADR 0004 |
| Automated emulator checks run on py-desmume in DS mode, on the builder's machine and never in CI; DSi-mode checks stay manual in melonDS | ADR 0005 |
| Patches carry the extracted content they add (one xdelta per game against the B2 ROM) | `07-open-questions.md`, Q1 |
| Every build fits DS mode (4 MB, DS Lite); DSi mode is never required | Q4 |
| Every game uses Gen 5 mechanics and B2W2's move data. Gen 5 decides how things work (battle and field rules, move data, species stats, types, abilities); the original game decides what is in it (story, dialogue, maps, trainers, encounters, items, learnsets, TM contents). No ruleset mechanism until a game needs a variant | Q6, Q9 (replace the brief's rulesets, Sections 4–5) |
| B2W2-only systems are per-game compile-time switches chosen in each game's config | Q7 |
| Original art and data are CC BY-SA 4.0; engine changes and tooling are GPL-3.0 | Q8; brief |
| Generic engine and tool work is offered upstream | Q10 |
