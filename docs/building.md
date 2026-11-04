# Building

`./kaleido` sets up, checks and builds a checkout (`docs/plan/03-architecture.md` §7). `extract`, `merge`, `validate`
and `patch` follow later in Phase 1. Every step here was run on the owner's machine (`docs/status.md`).

## Requirements

- **Linux or WSL2.** Upstream's build doesn't run on native Windows. Under WSL2, work in WSL's own filesystem
  (`~/…`), not on `/mnt/c`, which is far slower (R-23).
- **Packages** (Ubuntu 26.04): `sudo apt install ninja-build clang llvm python3.14-venv`. Python 3.11 or later; 3.14.4
  was used, upstream's CI uses 3.12.
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
   `engine/dsd/allow-stale-secure-area.patch` (R-27, ADR 0004). The first build takes about 35 minutes. `--skip-dsd`
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

`build` reads `content/games/<game>/game.json` and builds in the game's own engine worktree, `build/<game>/engine/`:
a git worktree at the engine's series, with the base ROM and `engine/pokebw2/tools/` linked in. It passes the game's
defines and `--allow-stale-secure-area`, builds the ROM target, and copies it to `build/<game>/kaleido-<game>.nds`.
Logs go to `build/<game>/logs/`. Until `kaleido merge` exists, a game is Black 2's content with its defines.

Both commands run `ninja` again while a dry run still has something to compile (R-28).

## 4. Options behind the commands

With Kaleido's patch series applied, `configure.py` also takes:

| Option | What |
| --- | --- |
| `--define NAME[=VALUE]` | A `KALEIDO_*` define for the code and scripts. The build no longer matches, so build the ROM target: `ninja build/pokeblack2_us.nds` |
| `--allow-stale-secure-area` | Needed whenever ARM9 main changes, code or data (R-27). DS mode ignores the stale values |
| `--arm7-bios PATH` | Instead of the flag above, if you have a DS ARM7 BIOS dump: every DSi value is then correct |

The defines the series knows so far are listed in [`engine/README.md`](../engine/README.md).

## Checks and pitfalls

- **Running `ninja` by hand, run it again until nothing is left to compile** after anything regenerates a header (a
  `generated/*.txt` list, a branch switch). One run can link objects built against the old constants and still finish
  the ROM (R-28, fix offered as fuddlesworth/pokebw2#807). `baseline` and `build` do this themselves.
- `python3 tools/build/verify_dsi_rom.py build/pokeblack2_us.nds` checks the DSi digests and HMACs. It skips the
  secure area's values by design.
- From Git Bash on Windows, a `/mnt/c/...` argument to `wsl.exe` is rewritten into a Windows path. Call `wsl.exe` from
  PowerShell, or set `MSYS_NO_PATHCONV=1`.
- Builds take minutes: run them in the background.
