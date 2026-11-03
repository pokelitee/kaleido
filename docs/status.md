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
  stopped on setup (path rewriting, no venv package, a checkout without `res/`). Upstream doesn't hash-check the
  Metrowerks compilers or objdiff; their hashes are now recorded. Details: `docs/research/e0-baseline.md`.

## Most important findings

1. Upstream's packers can **edit** the original map models and texture sets but can't **add** new ones (R-01).
   Chosen route (Q3): repurpose Unova chunks for the prototype, then an encoder that can add them; E4b confirms.
2. A single-source xdelta from B2 necessarily carries the extracted FRLG content; the owner accepted that (Q1).
   Patches still can't go on GitHub under the brief's rules; the channel is chosen before the first release.
3. B2W2 carts have infrared, a 512 KB FLASH save behind it, and 512 MB of ROM space at most. The game code must stay
   `IREO`. DS Protect must be guarded out in source (R-25).
4. FRLG's grass, surf and Super Rod odds, crit stages and type chart are identical to B2W2's (verified), so much of
   Gen 3 is data-exact.

## Next steps

1. Owner installs the build packages in WSL: `sudo apt install ninja-build clang llvm python3.14-venv`.
2. Owner copies the Black 2 (USA/Europe) dump to `~/kaleido-work/pokebw2/orig/baserom_b2_us.nds` in WSL (upstream's
   `.gitignore` covers it), and a FireRed dump to `~/kaleido-work/roms/` (its revision becomes the first extraction
   target, Q5).
3. E0 (baseline build), then E4b (new map art), E6, E1–E5, E8–E10 (`docs/plan/05-roadmap.md`). E7 waits for hardware.

## Blockers

- The WSL packages and the Black 2 and FireRed dumps are with the owner (E0 onward, E8).
- No hardware yet (E7; required by Phase 3.5's exit).

## Not verified in this pass

- No ROM was built: the base ROM isn't on this machine.
- Hardware facts come from GBATEK, emulator and loader sources, not from devices.
- xdelta determinism, the WSL file-system speed and upstream's tool hashes are untested assumptions (see `risks.md`).
