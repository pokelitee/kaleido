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

Not run yet. Needs, from the owner:

```bash
sudo apt install ninja-build clang llvm python3.14-venv
```

and the Black 2 (USA/Europe) dump at `~/kaleido-work/pokebw2/orig/baserom_b2_us.nds` (SHA1
`e51e6dfb8678a3d19dcd2a10691b96a569ca0abb`). Then:

```bash
cd ~/kaleido-work/pokebw2 && python3 configure.py b2_us && ninja
```

Done when `build/pokeblack2_us.nds` matches the SHA1, and a second clean build gives the same hash. Build time, disk
use and tool versions are recorded here.
