# Status

Last updated: 2026-11-03

## Current phase

**Phase 0 (experiments), started 2026-11-03** after the owner approved the plan. No game content, framework code or
engine changes exist yet. The owner's answers are in `docs/plan/07-open-questions.md`, and what is decided so far is
in `docs/architecture.md`.

Phase 0 work runs in a scratch pokebw2 checkout at the pin, in WSL's own filesystem (on the owner's machine,
`~/kaleido-work/pokebw2`). Experiment write-ups go in `docs/research/`.

## Done in this pass

- Researched the foundation and verified the brief's Section 3 baseline: `docs/research/` (pokebw2 pinned at
  `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c`, 2026-10-31).
- Wrote the plan: feasibility (`01`), foundation (`02`), architecture (`03`), roadmap (`05`), testing (`06`), open
  questions (`07`), and `docs/risks.md`.
- ADR 0001 (record decisions) accepted; ADR 0002 (engine integration) proposed, then accepted by the owner.
- Owner's answers to Q1–Q10 recorded. **Every game uses Gen 5 mechanics** and B2W2's move data; the ruleset mechanism
  is dropped until a game needs one (Q6, Q9). That replaces the brief's generation rulesets and two earlier answers
  the same day (per-game mechanic switches; a Gen 3 default for FRLG). B2W2-only systems are per-game compile-time
  switches (Q7). There is no hardware yet (Q4), so E7 moves out of the Phase 0 gate (`05-roadmap.md`).
- Planning pass merged to `main` (pokelitee/kaleido#1). The owner made the repository **public** on 2026-11-03 to
  unblock GitHub features. That settles the brief's [CONFIRM] default; see the table in `07-open-questions.md`.
- Repository settings: squash merges only; branches deleted after merge; secret scanning with push protection; a
  "Protect main" ruleset (pull request required, no force-push, no deletion, squash only, no bypass). The ruleset has
  no required CI check yet, because there is no CI; Phase 1 adds both (`05-roadmap.md`).
- Repo records: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/glossary.md`, `.gitignore` (ROMs, saves, build output,
  agent-local settings), `.gitattributes` (LF everywhere).
- **E0a passed** (Phase 0, 2026-11-03): upstream's `compile_all.py` at the pin compiled 3,584 of 3,584 (every C file,
  both versions) with no warnings, in WSL's filesystem with system Python 3.14.4. Three planning-pass attempts had
  stopped on setup (path rewriting, no venv package, a checkout without `res/`). Details:
  `docs/research/e0-baseline.md`.
- **E0 passed** (2026-11-03): with the owner's Black 2 dump, `configure.py b2_us && ninja` reproduced Black 2's SHA1
  (`e51e6dfb…`) twice from clean, in about 10–12 minutes each. Upstream doesn't hash-check dsd, objdiff or the
  Metrowerks compilers; all five downloaded tools' hashes are recorded for Kaleido's `doctor`.
- **E4b done** (2026-11-03): upstream's packers refuse new map models and texture sets. A ~25-line template-append
  prototype (`docs/research/e4b-template-append.patch`) built a ROM with a new chunk (#1065) and texture set (#409),
  with every original unchanged and valid DSi digests. It plays normally in melonDS in DS mode (owner's check). Found: `AREA_COUNT` caps areas at
  409; each chunk must fit its map type's buffer (86,020 B for most); recoloring shared texture data can be refused.
  ADR 0003 accepted. Details: `docs/research/e4b-map-art.md`.
- **E6a done** (2026-11-03, static): ROM ≈ 231 MiB free of 512 MiB; ARM9 binary far under the DSi's 2.5 MB. **DS-mode
  RAM is the constraint**: the heaps are fixed and the arena starts where the last overlay ends, so all added code and
  static data must fit in ≈ 213 KiB. Heap 1 has 288,256 B left in the field. E6b (runtime free memory, save use) is
  defined but not run. Details: `docs/research/e6-headroom.md`.
- **E1–E3 built, in-game checks partly pending** (2026-11-03). E3: `configure.py --define` plus a
  `KALEIDO_E3_ALWAYS_CRIT` switch. With the switch off, the build still matches Black 2 with every check; with it on,
  the compiled crit roll is always TRUE and 15 overlays move. E2: the rival's first party unpacks from the built ROM as
  Pikachu Lv 5. E1: the new intro text shows in game (owner). Pending: E1 glyph and line-width details; the rival
  battle in game (E2, E3). Details: `docs/research/e1-e3.md`.
- **E4a done** (2026-11-03): a new zone (header, events, warps both ways, script, text) packs and reads back from
  the built ROM. Appending zones collides with three hard-coded "no zone" values of 615; `KALEIDO_EXTRA_ZONES`
  fixes them, but it changes ARM9 main, which needs the DS ARM7 BIOS to finish the ROM (R-27). Resolved by ADR 0004
  (owner): Tier 1 reuses zone IDs, and Kaleido's dsd change `--allow-stale-secure-area` builds without the BIOS.
  With it, the untouched pin still matches Black 2, and E4a's ROM builds. Details: `docs/research/e4a-new-zone.md`.

## Most important findings

1. Upstream's packers can **edit** the original map models and texture sets but can't **add** new ones (R-01).
   Template-append adds them while keeping a template's materials and textures (E4b); a full encoder is needed
   before Phase 4 (ADR 0003).
2. A single-source xdelta from B2 necessarily carries the extracted FRLG content; the owner accepted that (Q1).
   Patches still can't go on GitHub under the brief's rules; the channel is chosen before the first release.
3. B2W2 carts have infrared, a 512 KB FLASH save behind it, and 512 MB of ROM space at most. The game code must stay
   `IREO`. DS Protect must be guarded out in source (R-25).
4. FRLG's grass, surf and Super Rod odds, crit stages and type chart are identical to B2W2's (verified), so much of
   Gen 3 is data-exact.

## Next steps

1. E5, E9 and E10 (`docs/plan/05-roadmap.md`), in `~/kaleido-work/pokebw2` (the E4b, E1–E3 and E4a prototypes are on
   branches `e4b-template-append`, `phase0-e1-e3` and `phase0-e4a`). E6b (runtime memory, save use) when an emulator harness or a
   melonDS GDB session is available.
2. Owner copies a FireRed dump to `~/kaleido-work/roms/` for E8; its revision becomes the first extraction target (Q5).
3. E7 waits for hardware.
4. Manual in-game checks are batched into a playtest pass at the end (owner's decision, 2026-11-03); the list is
   under "Deferred to playtesting" below.

## Blockers

- FireRed dump (E8 only).
- No hardware yet (E7; required by Phase 3.5's exit).

## Not verified yet

- Hardware facts come from GBATEK, emulator and loader sources, not from devices.
- xdelta determinism, and the determinism of modified builds and Kaleido's own tooling, are untested (see `risks.md`).

## Deferred to playtesting

Manual in-game checks are batched into one playtest pass at the end, not done after each experiment (owner's
decision, 2026-11-03). Experiments proceed on build-level verification. Until then:

| From | Check | Test ROM (never committed) |
| --- | --- | --- |
| E1 | Whether é ♂ ♀ ★ ♪ … all draw as glyphs, and how the over-long second line behaves (the new text itself shows) | `~/kaleido-work/e1-e3/kaleido-e1-e3-test.nds` |
| E2 | The rival at the Aspertia lookout sends out a level 5 Pikachu | same |
| E3 | Every damaging hit in that battle is "A critical hit!", with no crash, although 15 overlays moved | same |
| E4a | Aspertia City's door (warp 6) leads into the new zone: one NPC whose line is "Kaleido E4a: you're in a new zone."; the exit leads back; DS mode with stale secure-area values boots | `~/kaleido-work/e4a/kaleido-e4a-test.nds` |

Risk of waiting: a runtime-only break, such as code that fails after overlays move, surfaces later. Phase 1's emulator
harness (R-16) could run these checks automatically.
