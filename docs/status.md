# Status

Last updated: 2026-11-03

## Current phase

**Planning pass complete; the owner answered Q1–Q10 on 2026-11-03.** No game content, framework code or engine
changes exist yet. The answers are in `docs/plan/07-open-questions.md`, and what is decided so far is in
`docs/architecture.md`. Waiting on the owner's go-ahead for Phase 0 and the Phase 0 prerequisites.

## Done in this pass

- Researched the foundation and verified the brief's Section 3 baseline: `docs/research/` (pokebw2 pinned at
  `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c`, 2026-10-31).
- Wrote the plan: feasibility (`01`), foundation (`02`), architecture (`03`), roadmap (`05`), testing (`06`), open
  questions (`07`), and `docs/risks.md`.
- ADR 0001 (record decisions) accepted; ADR 0002 (engine integration) proposed, then accepted by the owner.
- Owner's answers to Q1–Q10 recorded. Two differ from the recommendations: mechanics where Gen 5 and the original
  differ (Q6) and B2W2-only systems (Q7) are per-game compile-time switches. There is no hardware yet (Q4), so E7
  moves out of the Phase 0 gate (`05-roadmap.md`).
- Planning pass merged to `main` (pokelitee/kaleido#1). The owner made the repository **public** on 2026-11-03 to
  unblock GitHub features. That settles the brief's [CONFIRM] default; see the table in `07-open-questions.md`.
- Repository settings: squash merges only; branches deleted after merge; secret scanning with push protection; a
  "Protect main" ruleset (pull request required, no force-push, no deletion, squash only, no bypass). The ruleset has
  no required CI check yet, because there is no CI; Phase 1 adds both (`05-roadmap.md`).
- Repo records: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/glossary.md`, `.gitignore` (ROMs, saves, build output,
  agent-local settings), `.gitattributes` (LF everywhere).
- E0a, no-ROM compile check of upstream's `compile_all.py` at the pin, in WSL2 (Ubuntu 26.04.1, Python 3.14.4):
  **not completed**. Stopped after three attempts, each failing on setup rather than compilation:
  1. Git Bash rewrote the `/mnt/c` path passed to `wsl.exe` (now noted in `CLAUDE.md`).
  2. `python3 -m venv` failed: WSL lacks `python3.14-venv`, which needs `sudo apt install python3.14-venv`.
  3. With system Python and a sparse checkout (everything except `res/`, plus `res/text/`), `compile_all.py` stopped
     on a missing `res/abilities/ability.schema.json`. The text banks' `\from{...}` lines read species, move,
     ability and trainer JSON, so a no-ROM compile needs those `res/` sources.

  What it showed:
  - A blobless clone of the pin onto `/mnt/c` took ~26 minutes (R-23).
  - Kaleido's CI compile job needs `res/` JSON from the public submodule, not just code (`06-testing.md`).
  - WSL needs `python3.14-venv` (Phase 0 prerequisites).

  E0a moves into Phase 0 with E0.

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

1. Owner gives the go-ahead for Phase 0.
2. Owner sets up Phase 0 prerequisites: `sudo apt install ninja-build clang llvm python3.14-venv` in WSL; a Black 2
   (USA/Europe) dump in WSL's own filesystem; a FireRed dump (its revision becomes the first extraction target, Q5).
3. Phase 0 experiments (`docs/plan/05-roadmap.md`), starting with E0 (baseline build) and E4b (new map art). E7 waits
   for hardware.

## Blockers

- Owner's go-ahead for Phase 0 (brief, Section 0).
- The Black 2 and FireRed dumps and the WSL packages are with the owner (E0, E8).
- No hardware yet (E7; required by Phase 3.5's exit).

## Not verified in this pass

- No ROM was built: the base ROM isn't on this machine.
- Hardware facts come from GBATEK, emulator and loader sources, not from devices.
- xdelta determinism, the WSL file-system speed and upstream's tool hashes are untested assumptions (see `risks.md`).
