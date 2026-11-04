# Building

Phase 1 is writing `kaleido doctor`, `bootstrap` and `build` (`docs/plan/03-architecture.md` §7). Until they exist,
this is the manual procedure. Its steps were run on the owner's machine in Phase 0 and Phase 1
(`docs/research/e0-baseline.md`, `e4a-new-zone.md`, `docs/status.md`).

## Requirements

- **Linux or WSL2.** Upstream's build doesn't run on native Windows. Under WSL2, work in WSL's own filesystem
  (`~/…`), not on `/mnt/c`, which is far slower (R-23).
- **Packages** (Ubuntu 26.04): `sudo apt install ninja-build clang llvm python3.14-venv`. Python 3.11 or later; 3.14.4
  was used, upstream's CI uses 3.12.
- **Rust**, through [rustup](https://rustup.rs) (minimal profile is enough), to build Kaleido's dsd. Only until upstream
  takes the change (ADR 0004).
- **Your own Black 2 (USA, Europe) dump**, SHA1 `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`.
- For extraction: your own source ROM. FireRed (USA) is SHA1 `41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc`; the others
  are in `docs/research/hardware-and-rom.md`.

Disk: about 3 GB for one checkout with one build (E0), plus Rust's build directory for dsd.

## 1. Kaleido and the engine

Clone Kaleido in WSL's filesystem, fetch the engine at the pin, and apply Kaleido's patch series:

```bash
cd ~ && git clone https://github.com/pokelitee/kaleido.git && cd kaleido
git submodule update --init --depth 1
cd engine/pokebw2
git switch -c kaleido
git am ../patches/*.patch
cp /path/to/your/black2.nds orig/baserom_b2_us.nds
sha1sum orig/baserom_b2_us.nds
```

`--depth 1` fetches only the pinned commit: 79 s and 1.2 GB on the owner's machine. Without it, git fetches the pin's
whole history (4,179 commits), because the pin isn't upstream's latest commit. `git am` needs a git identity
(`user.name`, `user.email`); with it, the engine's tree is the one Kaleido tested.

## 2. Kaleido's dsd

pokebw2's dsd refuses to finish a ROM whose ARM9 main changed, unless it has the DS ARM7 BIOS (R-27). Kaleido's dsd adds
`--allow-stale-secure-area` (`engine/dsd/allow-stale-secure-area.patch`, offered upstream as fuddlesworth/ds-rom#1 and
fuddlesworth/ds-decomp#2). `engine/engine.toml` names the commits it builds on.

```bash
mkdir -p ~/kaleido/.cache/dsd && cd ~/kaleido/.cache/dsd
for repo in ds-rom:66e83ef467b1e7a4816e667bf3b86572b1f8072d ds-decomp:2dc1b27b95fe9191ea9a0c2ea3145baa349125b8; do
  name=${repo%%:*}; commit=${repo#*:}
  git init -q "$name" && git -C "$name" remote add origin "https://github.com/fuddlesworth/$name.git"
  git -C "$name" fetch -q --depth 1 origin "$commit" && git -C "$name" checkout -q FETCH_HEAD
done
git apply ~/kaleido/engine/dsd/allow-stale-secure-area.patch
cd ds-decomp && cargo build --release --bin dsd
```

The first build takes about 35 minutes. The result, `ds-decomp/target/release/dsd`, had SHA256
`d19cbd9a2b85b7e173777de5839bb5d117ee6a74e2a5ede8edb45d6915ec3b37` on the owner's machine.

## 3. The matching baseline

```bash
cd ~/kaleido/engine/pokebw2
python3 configure.py b2_us --dsd ~/kaleido/.cache/dsd/ds-decomp/target/release/dsd
ninja
sha1sum build/pokeblack2_us.nds    # e51e6dfb8678a3d19dcd2a10691b96a569ca0abb
```

`configure.py` downloads the other tools into `tools/`. `ninja` extracts the ROM, compiles, links and rebuilds it, and
fails unless every matching check passes. A clean build takes 10–12 minutes.

## 4. Modified builds

With Kaleido's patch series applied, `configure.py` also takes:

| Option | What |
| --- | --- |
| `--define NAME[=VALUE]` | A `KALEIDO_*` define for the code and scripts. The build no longer matches, so build the ROM target: `ninja build/pokeblack2_us.nds` |
| `--allow-stale-secure-area` | Needed whenever ARM9 main changes, code or data (R-27). DS mode ignores the stale values |
| `--arm7-bios PATH` | Instead of the flag above, if you have a DS ARM7 BIOS dump: every DSi value is then correct |

The defines the series knows so far are listed in [`engine/README.md`](../engine/README.md).

## Checks and pitfalls

- **Run `ninja` again until nothing is left to compile** after anything regenerates a header (a `generated/*.txt`
  list, a branch switch). One run can link objects built against the old constants and still finish the ROM (R-28,
  fix offered as fuddlesworth/pokebw2#807).
- `python3 tools/build/verify_dsi_rom.py build/pokeblack2_us.nds` checks the DSi digests and HMACs. It skips the
  secure area's values by design.
- From Git Bash on Windows, a `/mnt/c/...` argument to `wsl.exe` is rewritten into a Windows path. Call `wsl.exe` from
  PowerShell, or set `MSYS_NO_PATHCONV=1`.
- Builds take minutes: run them in the background.
