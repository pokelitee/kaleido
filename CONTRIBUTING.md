# Contributing to Kaleido

Kaleido recreates other games of the series on the Black 2/White 2 engine ([pokebw2](https://github.com/fuddlesworth/pokebw2)).
Where the project stands is in [`docs/status.md`](docs/status.md). [`AGENTS.md`](AGENTS.md) is the canonical list of
rules for people and agents alike; this file covers how to work, and repeats the rules that matter most.

## Before you start

- Set up a build: [`docs/building.md`](docs/building.md). Builds run in Linux or WSL2, never native Windows.
- You need your own dumps: Black 2 (USA, Europe) for every build, and the source game's ROM for extraction. The
  expected SHA1s are in [`docs/research/hardware-and-rom.md`](docs/research/hardware-and-rom.md).

## Rules you must not break

- **Never commit ROMs or anything extracted from them**: `orig/`, `extract/`, `build/`, `dist/`, `*.nds`, `*.gba`,
  `*.gb`, `*.gbc`, saves, and other games' text, tables or graphics. That includes tests, fixtures, docs and commit
  messages. Fixtures are synthetic.
- **Never copy code, data files or labels from unlicensed projects**: the pret decomps, White2Upgrade, CTRMapV,
  SwissArmyKnife, FrostsGen5Editor. Read them for behavior and formats, then write your own.
- Every committed content file has exactly one provenance category (`docs/plan/03-architecture.md` §6). Third-party
  files need a license that permits our use, recorded in the layer's `provenance.json`.
- The project name is Kaleido. Don't put "Pokémon" or "Poké" in repo names, releases, file names or titles.

## Licensing

- Code (the framework, engine patches, tools): GPL-3.0, [`LICENSE`](LICENSE), as pokebw2 is.
- Original content (art, maps, scripts, data): CC BY-SA 4.0, [`LICENSE-CONTENT`](LICENSE-CONTENT).

By opening a pull request, you agree to license your contribution under these terms.

## Workflow

- Branch from `main`; never commit to `main`. The "Protect main" ruleset requires a pull request and allows squash
  merges only.
- CI must pass before a pull request merges (see Testing).
- Small commits in Conventional Commits form: `docs: …`, `feat(framework): …`, `fix(engine): …`.
- A pull request says what changed, why, and how it was tested. A check you couldn't run is named, not implied.
- Files use LF line endings (`.gitattributes`).
- When a rule changes, update `AGENTS.md`, this file and the affected docs in the same commit.

## Engine changes

- Engine changes live only as patches in `engine/patches/` (ADR 0002), each behavior change behind a `KALEIDO_*`
  define. With every define off, the engine must still rebuild Black 2 byte for byte.
- Inside engine code, follow pokebw2's rules: natural C, its `docs/code-standards.md`, clang-format 23.1.1.
- After `./kaleido bootstrap`, `git status` shows `engine/pokebw2` as changed: the engine's branch carries the series,
  in commits only your machine has. Never stage that pointer; only an engine sync moves it (`docs/engine-sync.md`).
  `./kaleido doctor` fails while it is staged.
- Any change to ARM9 main, code or data, needs `--allow-stale-secure-area` or `--arm7-bios` to finish the ROM (R-27).
- After changing a `generated/*.txt` list, run `ninja` again until nothing is left to compile (R-28).
- Generic changes are offered upstream first.

## Research and decisions

- Findings are tagged **Verified** (with source and commit or date), **Unverified** or **Assumption**. Never fill a
  gap from memory.
- Never claim a feature works, or was tested, without evidence.
- Decisions are ADRs in `docs/decisions/`. An accepted ADR is never edited; a new one supersedes it.

## Testing

Every pull request runs CI (`.github/workflows/ci.yml`), and its `CI` check must pass to merge. CI never sees a ROM
or anything made from one: no step, secret, cache or artifact may hold one. Before a pull request, run what it runs
(details in [`docs/building.md`](docs/building.md) §6):

```bash
./kaleido check
python3 -m unittest discover -s framework -t framework
```

and, for engine or content changes, `./kaleido compile` and `./kaleido validate <game> --no-extract`. Format Python
with Ruff, at the version in `framework/requirements-ci.txt`. Tests use `unittest` on synthetic fixtures
(`docs/plan/06-testing.md`). The checks that need the ROMs (`baseline`, `build`, `patch`) run on your machine: name the
ones you ran in the pull request. Checks that need playing the game are listed in `docs/status.md` under "Deferred to
playtesting".
