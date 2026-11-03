# Kaleido — agent and contributor guide

Kaleido recreates other games of the series (FireRed/LeafGreen first, then Red/Blue/Yellow) on the Black 2/White 2
engine, using the [pokebw2](https://github.com/fuddlesworth/pokebw2) decompilation. Each game builds to its own `.nds`
ROM for DS hardware and accurate emulators, and ships as an xdelta patch against the player's Black 2 ROM.

This file is the canonical, tool-neutral guide. `CLAUDE.md` imports it. **`docs/` is the source of truth**; this file
holds the rules sessions get wrong and points into `docs/`.

## Current phase

Planning is done, and the owner answered the open questions on 2026-11-03. **Do not build regions, gameplay systems or
framework code until the owner approves the plan.** Phase 0 experiments (`docs/plan/05-roadmap.md`) come next. Read
`docs/status.md` first.

## Where things are

| Need | Read |
| --- | --- |
| What is happening now, next steps, blockers | `docs/status.md` |
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

None yet. Phase 1 adds `kaleido doctor`, `bootstrap`, `extract`, `merge`, `validate`, `build`, `patch` and `baseline`
(`docs/plan/03-architecture.md` §7). Builds will run in Linux or WSL2, never native Windows; upstream requires it.

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

### Research and claims

- Tag every finding **Verified** (source plus commit or date), **Unverified**, or **Assumption**. If a source can't be
  fetched, say Unverified; never fill gaps from memory.
- Never claim a feature works, or was tested, without evidence.

### Records and git

- At the end of every session, commit the work and update `docs/status.md`. Leave no uncommitted state on a machine.
- An accepted ADR is never edited; supersede it with a new one (ADR 0001).
- When a rule changes, update `AGENTS.md`, `CONTRIBUTING.md` (Phase 1) and the affected docs in the same commit.
- Small commits in Conventional Commits form (`docs: …`, `feat(framework): …`). Work on feature branches; never commit
  to `main` directly.
- Files use LF line endings (`.gitattributes`).
- Add skills, subagents or hooks only after a procedure has been done by hand at least three times.
