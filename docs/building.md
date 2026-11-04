# Building

`./kaleido` sets up, checks, builds and patches a checkout (`docs/plan/03-architecture.md` §7). Every step here was run
on the owner's machine (`docs/status.md`).

## Requirements

- **Linux or WSL2.** Upstream's build doesn't run on native Windows. Under WSL2, work in WSL's own filesystem
  (`~/…`), not on `/mnt/c`, which is far slower (R-23).
- **Packages** (Ubuntu 26.04): `sudo apt install ninja-build clang llvm python3.14-venv xdelta3`. Python 3.11 or later;
  3.14.4 was used, upstream's CI uses 3.12. xdelta3 is only for `kaleido patch`.
- **Rust**, through [rustup](https://rustup.rs) (minimal profile is enough), for `bootstrap` to build Kaleido's dsd.
  Only until upstream takes the change (ADR 0004).
- **Your own Black 2 (USA, Europe) dump**, SHA1 `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`.
- For extraction: your own source ROM. FireRed (USA) is SHA1 `41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc`; the others
  are in `docs/research/hardware-and-rom.md`.

Disk: about 3 GB for one checkout with one build (E0), plus Rust's build directory for dsd.

## 1. Set up

Clone Kaleido in WSL's filesystem, put your ROMs in `orig/` (ignored by git), then bootstrap:

```bash
cd ~ && git clone https://github.com/pokelitee/kaleido.git && cd kaleido
mkdir -p orig && cp /path/to/your/black2.nds orig/black2.nds
./kaleido bootstrap
./kaleido doctor
```

For extraction, also `orig/firered.gba`. Nothing needs installing: `./kaleido` runs the framework from the checkout.

`bootstrap` does each step only if it isn't done already:

1. Checks `engine/pokebw2` out at the pin, fetching only that commit (`--depth 1`: about 80 s and 1.2 GB; without it
   git fetches the pin's 4,179-commit history).
2. Applies `engine/patches/` with `git am` on the engine's branch `kaleido`. The commits are the same on every machine.
   It refuses to discard uncommitted engine changes, or engine commits not exported to `engine/patches/`, unless
   given `--force`.
3. Links `engine/pokebw2/orig/baserom_b2_us.nds` to `orig/black2.nds`.
4. Builds Kaleido's dsd into `.cache/dsd/`: ds-rom and ds-decomp at the commits in `engine/engine.toml`, plus
   `engine/dsd/allow-stale-secure-area.patch` (R-27, ADR 0004). The first build took about 35 minutes on a machine
   with no Rust crates downloaded, and about 3 minutes in a second clone once cargo had them. `--skip-dsd`
   leaves it out.

`doctor` checks the platform, Python, the commands upstream's build calls, disk space, the engine, dsd, the ROMs'
SHA1s, and the SHA256s of the tools pokebw2 downloads (recorded in `engine/engine.toml`, R-12). It prints how to fix
each problem and exits 1 if anything fails.

## 2. The matching baseline

```bash
./kaleido baseline
```

The patched engine, every define off, must still rebuild Black 2 byte for byte (`e51e6dfb…`). `baseline` runs
`configure.py b2_us` in `engine/pokebw2` with Kaleido's dsd, then `ninja` with every one of upstream's matching
checks, and exits 1 unless the ROM's SHA1 matches. The first run downloads upstream's other tools into
`engine/pokebw2/tools/`, which `doctor` then checks. A clean build takes about 10 minutes. Logs go to
`build/baseline/logs/`.

## 3. A game

```bash
./kaleido build firered
```

`build` reads `content/games/<game>/game.json`. It needs the game's source ROMs in `orig/` (FireRed:
`orig/firered.gba`). The steps:

1. **Worktree:** the game's own engine worktree, `build/<game>/engine/`, at the engine's series, with the base ROM and
   `engine/pokebw2/tools/` linked in. It belongs to Kaleido: don't edit it by hand.
2. **Extract:** the layers' recipes run on the source ROMs into `build/<game>/extracted/`.
3. **Merge:** the layers, lowest first, are laid over the worktree's `res/` and `generated/`.
   `build/<game>/merge-report.json` lists every merged file with its layers and provenance.
4. **Build:** the game's defines and `--allow-stale-secure-area` go to `configure.py`, ninja builds the ROM target, and
   the ROM is copied to `build/<game>/kaleido-<game>.nds`. Logs go to `build/<game>/logs/`.

Between merge and build, `validate` checks the merged tree's cross-references and stops the build on a problem.

`./kaleido extract <game>`, `merge <game>` and `validate <game>` run the first steps alone, to look at their output.
`validate <game> --no-extract` skips extraction and merges only the committed layer files, as CI does (section 6).

## 4. A patch

```bash
./kaleido patch firered
```

`patch` makes `dist/kaleido-<game>.xdelta` from `orig/black2.nds` and the built ROM. It applies the patch to the base
ROM and checks the result is the built ROM, then writes `dist/kaleido-<game>.sha1` with the base ROM's, the patch's and
the result's SHA1s. It needs xdelta3 3.0.11 (`sudo apt install xdelta3`), whose patches don't depend on file names with
the options Kaleido passes. The patch carries the game's extracted content (Q1): `dist/` is never committed, and where
patches are published is decided before the first release (R-06).

Both commands run `ninja` again while a dry run still has something to compile (R-28).

## 5. Options behind the commands

With Kaleido's patch series applied, `configure.py` also takes:

| Option | What |
| --- | --- |
| `--define NAME[=VALUE]` | A `KALEIDO_*` define for the code and scripts. The build no longer matches, so build the ROM target: `ninja build/pokeblack2_us.nds` |
| `--allow-stale-secure-area` | Needed whenever ARM9 main changes, code or data (R-27). DS mode ignores the stale values |
| `--arm7-bios PATH` | Instead of the flag above, if you have a DS ARM7 BIOS dump: every DSi value is then correct |

The defines the series knows so far are listed in [`engine/README.md`](../engine/README.md).

## 6. The checks CI runs

CI ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) runs on every pull request and every push to `main`,
and never sees a ROM. Its `CI` check passes only when both of its jobs do:

- **Framework**, on Python 3.11 (the oldest Kaleido supports): Ruff's format and lint checks, the unit tests (with
  xdelta3 installed, so the real round trip runs), and `./kaleido check`.
- **Engine**, on Python 3.12 (as upstream's CI): `./kaleido bootstrap --skip-dsd`, clang-format 23.1.1 on the C files
  the series changes, `./kaleido compile`, and `./kaleido validate <game> --no-extract` for each game. It caches
  `engine/pokebw2/tools/`, keyed on `engine/engine.toml`.

The same checks on your machine:

```bash
./kaleido check
python3 -m unittest discover -s framework -t framework
./kaleido compile
./kaleido validate firered --no-extract
```

- `check` needs neither a ROM nor the engine. Its ROM-content guard reads every tracked file: nothing under `orig/`,
  `extract/`, `build/` or `dist/`; no ROM, save, patch or emulator savestate by extension, or by a DS, GBA, Game Boy or
  VCDIFF header;
  nothing over 1 MiB. It also loads every layer (provenance, recipes) and game config, and follows every link between
  Markdown files.
- `compile` runs upstream's `tools/decomp/compile_all.py` for Black 2, once with every define off and once per distinct
  set of game defines (patch `0004`). It needs the engine but no ROM: about 90 seconds per set on 12 cores once the tools
  are downloaded.
- Ruff and clang-format: in a virtual environment, `pip install -r framework/requirements-ci.txt`, then `ruff format
  framework` and `ruff check framework`.

Dependabot ([`.github/dependabot.yml`](../.github/dependabot.yml)) proposes weekly, grouped updates of the actions
and of Ruff. clang-format stays at upstream's 23.1.1, and the engine pin moves only through `docs/engine-sync.md`.

## Checks and pitfalls

- **Running `ninja` by hand, run it again until nothing is left to compile** after anything regenerates a header (a
  `generated/*.txt` list, a branch switch). One run can link objects built against the old constants and still finish
  the ROM (R-28, fix offered as fuddlesworth/pokebw2#807). `baseline` and `build` do this themselves.
- `python3 tools/build/verify_dsi_rom.py build/pokeblack2_us.nds` checks the DSi digests and HMACs. It skips the
  secure area's values by design.
- From Git Bash on Windows, a `/mnt/c/...` argument to `wsl.exe` is rewritten into a Windows path. Call `wsl.exe` from
  PowerShell, or set `MSYS_NO_PATHCONV=1`.
- Builds take minutes: run them in the background.
