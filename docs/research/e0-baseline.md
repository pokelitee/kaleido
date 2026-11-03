# E0 — Baseline build of pokebw2

Phase 0 experiment (`docs/plan/05-roadmap.md`). Goal: prove pokebw2 builds at the pin on the owner's machine, first
without a ROM (E0a, compile only), then with the Black 2 dump (E0, full matching build).

- pokebw2 commit: `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c` (2026-10-31)
- Machine: Windows 11 Pro 10.0.22631, WSL2 kernel 6.18.54.1-microsoft-standard-WSL2, Ubuntu 26.04.1 LTS, Python 3.14.4,
  12 CPUs, 15 GB RAM
- Location: `~/kaleido-work/pokebw2` in WSL's own ext4 filesystem (not `/mnt/c`, R-23)

## E0a — compile every C file without a ROM

### Method

Fetch only the pinned commit, then run upstream's own no-ROM check as its CI does:

```bash
mkdir -p ~/kaleido-work/pokebw2 && cd ~/kaleido-work/pokebw2
git init -q && git remote add origin https://github.com/fuddlesworth/pokebw2.git
git fetch --depth 1 origin 41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c && git checkout FETCH_HEAD
python3 tools/decomp/compile_all.py -j 10
```

`compile_all.py` downloads wibo, sjiswrap and the Metrowerks compilers into `tools/`, generates the constant and text
headers, and compiles every source file for both versions. ROM blobs compile as zeros.

### Earlier attempts (planning pass, 2026-11-03)

Three attempts in the planning pass stopped on setup, never reaching compilation:

1. Git Bash rewrote the `/mnt/c` path passed to `wsl.exe` (`CLAUDE.md` now says how to avoid it).
2. `python3 -m venv` needs `python3.14-venv`, which isn't installed.
3. A sparse checkout without `res/` failed: text banks pull lines from `res/` JSON through `\from{...}`.

### Result (2026-11-03): passed

**Verified** on the owner's machine:

| Step | Result |
| --- | --- |
| Depth-1 fetch of the pin into ext4 | 114 s; 145,253 files; 1.2 GB working tree |
| `compile_all.py -j 10` | **3,584 of 3,584 compiled** (1,792 files × Black 2 and White 2), exit 0, 316 s |
| Compiler warnings | none (`compile_all.py` fails on any warning) |
| Python | system Python 3.14.4 works; no venv needed for this step |

Tools `compile_all.py` downloaded, with SHA256s recorded here so later runs can be compared:

| Tool | Version | SHA256 | Hash checked by upstream? |
| --- | --- | --- | --- |
| wibo | `pokebw2-sjis-1` | `d708570bd64cc8c176273a2bb7b5082f4fa849139d0ffe6cd0b96e26f3bc1ef2` | Yes (`WIBO_SHA256`) |
| sjiswrap | `v1.2.2-pokebw2.1` | `4e9c917ba3f245da74a5a48ec91b459e956189cc1411233aa40046e0f7ac294f` | Yes (`SJISWRAP_SHA256`) |
| objdiff-cli | `v3.8.1` | `c8290281e82114bcc1a06ff73061110d3902a177822e750337de2537188e358f` | **No** (`urlretrieve`, no check) |
| mwccarm (`1.2/`, `2.0/`, `dsi/`, 47 MB) | from `decomp.aetias.com/files/mwccarm.zip` | tree digest `16fa8cfe8b3bf2ed1f1e03068cd4b56edf9ecb5f8ee6ede48c2c04566f6471ff` (SHA256 of the sorted `sha256sum` lines of every file) | **No** (`urlopen`, no check) |

What this settles:

- The toolchain runs on Ubuntu 26.04 under WSL2 with Python 3.14 (R-18, in part: no ROM build yet).
- Kaleido's CI compile job is feasible as designed: a full `res/` checkout of the public submodule, no ROM
  (`06-testing.md`).
- Upstream doesn't verify objdiff or the Metrowerks compilers. Kaleido's `doctor` and tool cache must pin those two
  hashes itself (R-12).
- Working in WSL's filesystem is fast: 114 s for a depth-1 fetch, against ~26 min for a blobless clone with full
  history onto `/mnt/c` in the planning pass. The two runs fetched different amounts, so this shows the
  approach works, not a precise speedup (R-23).

## E0 — matching build with the Black 2 dump

### Method

The owner installed the build packages (`sudo apt install ninja-build clang llvm python3.14-venv`) and supplied the
Black 2 (USA/Europe) dump. It was copied to `~/kaleido-work/pokebw2/orig/baserom_b2_us.nds`, and its SHA1 was checked
both before and after the copy. Then, twice, each time from clean (removing `build/`, `build.ninja` and ninja's state):

```bash
cd ~/kaleido-work/pokebw2 && python3 configure.py b2_us && ninja
```

`ninja` extracts and delinks the ROM, compiles, links, rebuilds the ROM and fails unless its SHA1 matches.

### Result (2026-11-03): passed

**Verified** on the owner's machine:

| | Run 1 | Run 2 |
| --- | --- | --- |
| `configure.py b2_us` | 77 s | 168 s |
| `ninja` (7,626 steps) | 497 s | 540 s |
| Output `build/pokeblack2_us.nds` SHA1 | `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb` | `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb` |
| `build/` size | 1006 MB | 1006 MB |

- **Both clean builds reproduce Black 2 byte for byte.** A matching build is deterministic by construction, so the
  second run mainly confirms that nothing depends on leftover state.
- `ninja progress`: code 3,867,578 / 3,867,578 bytes, functions 43,418 / 43,418, files 1,792 / 1,800 complete. This
  agrees with ByteMatch (`hardware-and-rom.md`).
- The whole checkout with one build is 3.1 GB.
- Tool versions: ninja 1.13.2; Ubuntu clang and LLVM 21.1.8; Python 3.14.4; dsd (`ds-decomp-cli`) 0.12.1, release
  `v0.12.1-dsi.10`, SHA256 `f344007027f6c86c951c81c70d5e7964ef8e6bb56157fbaefb4fc879a39ff2ac`. Upstream downloads dsd
  with `urlretrieve` and **no hash check** (`configure.py`, `get_dsd`), like objdiff and the Metrowerks compilers.
- Run 2's configure took twice as long as run 1's. Both ran on the same machine with nothing else scheduled; the cause
  wasn't investigated.

### What this settles

- The matching build works on the owner's machine with Python 3.14, against upstream CI's 3.12 (R-18, in part).
- `kaleido baseline` (`03-architecture.md` §7) is achievable as designed. The patched engine with every define off has
  a known target: `e51e6dfb…`.
- A full clean build costs about 10–12 minutes and 1 GB of `build/`. A Phase 1 per-game engine worktree costs about
  3 GB with one build.
- Three of upstream's five downloaded tools (dsd, objdiff, the Metrowerks compilers) aren't hash-checked by
  upstream. Kaleido's `doctor` pins all five (R-12).
