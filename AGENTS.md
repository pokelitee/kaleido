# Kaleido — agent and contributor guide

Kaleido recreates other games of the series (FireRed/LeafGreen first, then Red/Blue/Yellow) on the Black 2/White 2
engine, using the [pokebw2](https://github.com/fuddlesworth/pokebw2) decompilation. Each game builds to its own `.nds`
ROM for DS hardware and accurate emulators, and ships as an xdelta patch against the player's Black 2 ROM.

This file is the canonical, tool-neutral guide. `CLAUDE.md` imports it. **`docs/` is the source of truth**; this file
holds the rules sessions get wrong and points into `docs/`.

## Current phase

**Phase 1** (framework skeleton) since 2026-11-04, when the owner closed Phase 0 and moved E6b into Phase 1's emulator
harness spike. Phase 1 builds the repo layout, the engine submodule and its first patches, the `kaleido` commands,
layer merge, CI and Dependabot (`docs/plan/05-roadmap.md`). **No region content beyond Phase 1's tiny test layer until
Phase 3.** Phase 0's prototypes and findings are in `docs/research/`. Read `docs/status.md` first.

## Where things are

| Need | Read |
| --- | --- |
| What is happening now, next steps, blockers | `docs/status.md` |
| Workflow and licensing for contributors | `CONTRIBUTING.md` |
| Building by hand (until `kaleido` exists) | `docs/building.md` |
| Moving the engine pin | `docs/engine-sync.md` |
| Feasibility, Exact/Approximate/Infeasible tables | `docs/plan/01-feasibility.md` |
| Tools used and excluded, with licenses | `docs/plan/02-foundation.md` |
| Repo layout, layering, provenance, build pipeline | `docs/plan/03-architecture.md` |
| Phases, experiments (E0–E10), acceptance criteria | `docs/plan/05-roadmap.md` |
| Test strategy and the CI/local split | `docs/plan/06-testing.md` |
| Owner's answers to Q1–Q10 | `docs/plan/07-open-questions.md` |
| What is decided and built so far | `docs/architecture.md` |
| Risks (R-01…) | `docs/risks.md` |
| Decisions | `docs/decisions/` (ADRs) |
| Research findings with evidence tags | `docs/research/` |
| Terms | `docs/glossary.md` |

## Commands

From the repository's root, in Linux or WSL2 (never native Windows; upstream requires it):

| Command | What |
| --- | --- |
| `./kaleido bootstrap` | engine at the pin, the patch series on branch `kaleido`, the base ROM linked, Kaleido's dsd built |
| `./kaleido doctor` | checks the machine, engine, dsd, ROMs and downloaded tools; exits 1 on a failure |
| `./kaleido baseline` | the patched engine, every define off, must rebuild Black 2 byte for byte |
| `./kaleido extract <game>` | the game's layers' recipes, run on your source ROMs, into `build/<game>/extracted/` |
| `./kaleido merge <game>` | extracts, then lays the game's layers over its engine worktree, `build/<game>/engine/` |
| `./kaleido validate <game>` | extracts, merges, then checks the merged tree's cross-references |
| `./kaleido build <game>` | extracts, merges, validates and builds the ROM: `build/<game>/kaleido-<game>.nds` |
| `./kaleido patch <game>` | `dist/kaleido-<game>.xdelta` against your Black 2, checked by applying it (xdelta3 3.0.11) |
| `python3 -m unittest discover -s framework -t framework` | the framework's tests |

Details: `docs/building.md`; layers and their rules: `content/README.md`.

## Rules

### Legal and provenance

- **Never commit ROMs or anything extracted from them.** That covers `orig/`, `extract/`, `build/`, `dist/`, `*.nds`,
  `*.gba`, `*.gb`, `*.gbc`, saves, and other-game text, tables or graphics, even in tests, fixtures, docs or commit
  messages. Test fixtures are synthetic.
- **Never copy code, data files or labels from unlicensed projects**: the pret decomps (pokered, pokefirered, …),
  White2Upgrade, CTRMapV, SwissArmyKnife, FrostsGen5Editor. Read them for behavior and formats, then write our own.
  GPL-3.0 sources (pokebw2, CTRMap-CE, swan, PMC) may be reused under GPL-3.0 with attribution.
- Every committed content file has exactly one provenance category: upstream, extracted, original or third-party
  (`docs/plan/03-architecture.md` §6). Third-party files need a recorded license that permits our use.
- The project name is **Kaleido**. Never add "Pokémon" or "Poké" to repo names, releases, file names or titles.
- Engine code and tooling are GPL-3.0 (required by pokebw2). Original art and data are CC BY-SA 4.0 (Q8).

### Engine

- Engine changes live only as patches in `engine/patches/` (ADR 0002). Every behavior change sits behind a
  `KALEIDO_*` define. With all defines off, the patched engine must still rebuild Black 2 byte for byte.
- Follow pokebw2's own rules inside engine code: natural C, its `docs/code-standards.md`, clang-format 23.1.1, English
  names. Upstream's agent setup (`.claude/` in pokebw2) and its "push to main" workflow are **not** ours.
- Never assume a mechanic exists in the engine. Prove it with an experiment and record it in `docs/research/`.
- Respect DS limits: RAM, overlays, ROM and save sizes are measured (E6), not assumed.
- Tier 1 zones reuse existing zone IDs; don't append zones (ADR 0004). A build that changes anything in ARM9 main, code
  or data, needs `--allow-stale-secure-area` (Kaleido's dsd) or `--arm7-bios` (R-27).
- Each game has its own `KALEIDO_SAVE_MAGIC`; never reuse Black 2's or another game's (E9).
- After changing a `generated/*.txt` list or anything else that regenerates a header, run `ninja` again until nothing is
  left to compile. One run can link objects built against the old constants and still finish the ROM (R-28).

### Research and claims

- Tag every finding **Verified** (source plus commit or date), **Unverified**, or **Assumption**. If a source can't be
  fetched, say Unverified; never fill gaps from memory.
- Never claim a feature works, or was tested, without evidence.

### Records and git

- At the end of every session, commit the work and update `docs/status.md`. Leave no uncommitted state on a machine.
- An accepted ADR is never edited; supersede it with a new one (ADR 0001).
- When a rule changes, update `AGENTS.md`, `CONTRIBUTING.md` and the affected docs in the same commit.
- Small commits in Conventional Commits form (`docs: …`, `feat(framework): …`). Work on feature branches; never commit
  to `main` directly.
- Files use LF line endings (`.gitattributes`).
- Add skills, subagents or hooks only after a procedure has been done by hand at least three times.
