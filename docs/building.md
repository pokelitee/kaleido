# Building

Phase 1 is writing `kaleido doctor`, `bootstrap` and `build` (`docs/plan/03-architecture.md` §7). Until they exist,
this is the manual procedure Phase 0 used. Every step below was run on the owner's machine (`docs/research/e0-baseline.md`,
`e4a-new-zone.md`).

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

## 1. pokebw2 at the pin

```bash
mkdir -p ~/kaleido-work/pokebw2 && cd ~/kaleido-work/pokebw2
git init -q && git remote add origin https://github.com/fuddlesworth/pokebw2.git
git fetch --depth 1 origin 41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c && git checkout FETCH_HEAD
cp /path/to/your/black2.nds orig/baserom_b2_us.nds
sha1sum orig/baserom_b2_us.nds
```

The fetch takes about 2 minutes. `engine/pokebw2` replaces this checkout once the submodule is in.

## 2. Kaleido's dsd

pokebw2's dsd refuses to finish a ROM whose ARM9 main changed, unless it has the DS ARM7 BIOS (R-27). Kaleido's dsd adds
`--allow-stale-secure-area` (`docs/research/dsd-allow-stale-secure-area.patch`, offered upstream as
fuddlesworth/ds-rom#1 and fuddlesworth/ds-decomp#2).

```bash
mkdir -p ~/kaleido-work/dsd-src && cd ~/kaleido-work/dsd-src
for repo in ds-rom:66e83ef467b1e7a4816e667bf3b86572b1f8072d ds-decomp:2dc1b27b95fe9191ea9a0c2ea3145baa349125b8; do
  name=${repo%%:*}; commit=${repo#*:}
  git init -q "$name" && git -C "$name" remote add origin "https://github.com/fuddlesworth/$name.git"
  git -C "$name" fetch -q --depth 1 origin "$commit" && git -C "$name" checkout -q FETCH_HEAD
done
git apply /path/to/kaleido/docs/research/dsd-allow-stale-secure-area.patch
cd ds-decomp && cargo build --release --bin dsd
```

The first build takes about 35 minutes. The result, `ds-decomp/target/release/dsd`, had SHA256
`d19cbd9a2b85b7e173777de5839bb5d117ee6a74e2a5ede8edb45d6915ec3b37` on the owner's machine.

## 3. The matching baseline

```bash
cd ~/kaleido-work/pokebw2
python3 configure.py b2_us --dsd ~/kaleido-work/dsd-src/ds-decomp/target/release/dsd
ninja
sha1sum build/pokeblack2_us.nds    # e51e6dfb8678a3d19dcd2a10691b96a569ca0abb
```

`configure.py` downloads the other tools into `tools/`. `ninja` extracts the ROM, compiles, links and rebuilds it, and
fails unless every matching check passes. A clean build takes 10–12 minutes.

## 4. Modified builds

Kaleido's defines and dsd flags come with the first engine patches (`engine/patches/`, next in Phase 1). With them,
`configure.py` takes:

| Option | What |
| --- | --- |
| `--define NAME[=VALUE]` | A `KALEIDO_*` define for the code and scripts. The build no longer matches, so build the ROM target: `ninja build/pokeblack2_us.nds` |
| `--allow-stale-secure-area` | Needed whenever ARM9 main changes, code or data (R-27). DS mode ignores the stale values |
| `--arm7-bios PATH` | Instead of the flag above, if you have a DS ARM7 BIOS dump: every DSi value is then correct |

Phase 0's versions of these patches are in `docs/research/`.

## Checks and pitfalls

- **Run `ninja` again until nothing is left to compile** after anything regenerates a header (a `generated/*.txt`
  list, a branch switch). One run can link objects built against the old constants and still finish the ROM (R-28,
  fix offered as fuddlesworth/pokebw2#807).
- `python3 tools/build/verify_dsi_rom.py build/pokeblack2_us.nds` checks the DSi digests and HMACs. It skips the
  secure area's values by design.
- From Git Bash on Windows, a `/mnt/c/...` argument to `wsl.exe` is rewritten into a Windows path. Call `wsl.exe` from
  PowerShell, or set `MSYS_NO_PATHCONV=1`.
- Builds take minutes: run them in the background.
