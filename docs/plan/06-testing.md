# 06 — Testing

Status: **proposal** for owner review (planning pass, 2026-11-03).

## The split

**CI must never see a ROM or anything derived from one** (brief, Section 6). That includes secrets, caches and
artifacts. So tests fall into two groups:

| Where | What it can check | What it can't |
| --- | --- | --- |
| GitHub Actions (no ROMs) | Code quality, framework logic, schemas, provenance, cross-references between our files, that the patched engine compiles for every game's defines | Anything that needs extracted data, a built ROM, or upstream archives built from the base ROM |
| Local (owner's machines, ROMs in `orig/`) | Matching baseline, game builds, determinism, extraction, ROM validation, emulator tests, hardware | — |

A self-hosted runner under the owner's control could take over the local ROM checks later, if the owner approves one
(brief, Section 6). The plan doesn't depend on it.

## Layer 1: CI (every push and pull request)

One required check, `CI`, running these jobs:

| Check | How | Notes |
| --- | --- | --- |
| Python format and lint | Ruff | `framework/` |
| Engine C format | clang-format 23.1.1 on the patched files | Matches upstream's Standards workflow |
| Framework unit tests | `unittest` (stdlib, as upstream uses) on synthetic fixtures | Merge rules, merge patches, constant-list appends, provenance matching, recipe parsing, extractor decoding (on synthetic byte strings shaped like the source format, never ROM bytes) |
| Schema validation | Every committed layer file against upstream's schemas plus ours | Upstream's schemas come from the public submodule, which has no ROM content |
| Provenance | Every committed path covered exactly once; no category 2 path in git; category 4 entries carry a license | — |
| Cross-references | Run on committed layers plus upstream `res/`, with extracted IDs taken from recipes (the IDs are declared there, the content isn't) | Catches broken warps, unknown constants and missing text IDs without ROM data |
| ROM-content guard | Reject ROM and save files by extension and by magic bytes, files over a size limit, and anything under `orig/`, `extract/` or `build/` | Also a pre-commit hook |
| Engine compile | Apply the patch series, then run upstream's `compile_all.py` once per distinct define set (baseline, each game) | Needs no ROM: ROM blobs compile as zeros (upstream's own CI does this). Needs upstream's `res/` JSON, because text banks pull lines from it (found in E0a), so the job checks out the public submodule with `res/`. Downloads the Metrowerks tools; cached by `actions/cache` |
| Docs | Links between `docs/` files resolve | Cheap; keeps the records usable |

CI hygiene follows the owner's standard: actions pinned to full commit SHAs with a version comment, read-only
`permissions`, `timeout-minutes` on every job, no artifact uploads from build steps.

## Layer 2: local ROM checks (before merging engine or content changes)

`kaleido test --local` runs them in this order. Each stops at the first failure and names the file.

1. **Doctor**: tool versions and hashes, ROM SHA1s.
2. **Baseline**: patched engine, all defines off, no layers → Black 2 SHA1 `e51e6dfb…`. Required for any change to
   `engine/patches/` and for every upstream sync.
3. **Extraction**: each game's extracted tree hashes to the value recorded locally for its source ROM revision.
   Extraction runs twice and must give the same bytes.
4. **Build**: each game builds. The result is checked for:
   - **Determinism**: a second clean build gives the same ROM SHA1.
   - **ROM validation**: header CRCs, DSi digests and HMACs (upstream's `verify_dsi_rom.py`), ROM ≤ 512 MB, ARM9 ≤
     2.5 MB, overlay table sanity, game code unchanged.
   - **Patch round trip**: `xdelta3 -d` of the patch on the base ROM gives the built ROM's SHA1.
5. **Golden hashes**: the expected SHA1 of each game's ROM and patch is recorded locally per release candidate. A
   change that alters a hash without an intended content or engine change is a regression.

## Layer 3: emulator tests

Manual in-game checks are batched into a playtest pass at the end, not run after each change (owner's decision,
2026-11-03). Pending ones are listed in `docs/status.md`. Automated emulator tests, once the harness exists, run as
part of the local checks.

melonDS is the primary emulator, DeSmuME secondary (brief). Neither has a headless scripting mode on Linux
(`docs/research/hardware-and-rom.md`). Phase 1 includes a short spike to pick the harness:

- **py-desmume** (GPL-3.0, wraps DeSmuME's C interface): headless, scriptable from Python, memory read/write and
  savestates. DS mode only.
- **A minimal harness on melonDS's core library**: DS and DSi mode, more work.
- **BizHawk** with Lua: works, but its licensing is unclear and it needs Mono. A tool we run, not one we ship, so
  usable if the others fail.

Spike result (2026-11-04): py-desmume drove Black 2 headless to the first battle and measured E6b
(`docs/research/harness-spike.md`). ADR 0005 proposes it for DS mode, with DSi-mode checks manual in melonDS.

Tests the harness runs, from scripted input and RAM reads:

| Test | Asserts |
| --- | --- |
| Boot smoke | Title screen reached; no crash for N frames; DS mode and DSi mode |
| New game | Start zone is the game's (Pallet Town); player in the right place |
| Save/load round trip | Save, reset, load: position, party, flags, bag match |
| Foreign save | A B2 save and another Kaleido game's save are refused (E9) |
| Warp graph | Walk each warp in a zone list; arrive at the declared warp |
| Scripted battle | With a fixed RNG seed: damage, crits and turn order match the unmodified B2W2 engine's, so Kaleido's changes haven't altered Gen 5 mechanics |
| Encounter odds | Many forced encounters: slot frequencies within tolerance of the table |
| Anti-piracy | Play past known checks: no anti-piracy effects |

**Host-compiled battle math** (optional): pokebw2's C is natural, portable C. If a Kaleido patch ever touches battle
code, pure functions such as `CalcBaseDamage` and the crit and type-effectiveness helpers in `src/ov167/btl_calc.c`
can be compiled with the host compiler and unit-tested in CI, with no ROM. With Gen 5 mechanics unchanged (Q6), this is
not planned work.

## Layer 4: hardware

Manual, from a checklist kept in `docs/testing/hardware.md` (Phase 3.5), for each release candidate and after E7:

- Each device the owner has (Q4), in DS mode and, where possible, DSi mode, through each loader used in E7.
- Boot, new game, play 30 minutes, save, power off, power on, load.
- Sleep mode (close the lid) and resume.
- Infrared and Wi-Fi features are disabled and can't be reached (Q7).
- No anti-piracy effects (R-25).
- Results are recorded with the ROM SHA1, device, loader and loader version.

## Fidelity tests

Each feature in `01-feasibility.md` gets a test once it is built: Exact features get an automated assertion where
the harness can reach them, otherwise a checklist line. Approximate features record the difference that is expected.

## What isn't tested

- Real cartridges: Kaleido runs from flashcarts, loaders and emulators only.
- Online features: disabled (Q7).
- Every Exact claim by playthrough: Phase 4 runs full playthroughs, but much fidelity is checked by data comparison
  against the extracted source tables, not by play.
