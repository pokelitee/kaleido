# 02 — Foundation: tools to use and exclude

Status: **proposal** for owner review (planning pass, 2026-11-03). Evidence for every row is in
`docs/research/pokebw2.md`, `docs/research/peripheral-tools.md` and `docs/research/hardware-and-rom.md`, with commits
and dates.

## Use

| Tool | Role | License | Pinned at | Why |
| --- | --- | --- | --- | --- |
| [fuddlesworth/pokebw2](https://github.com/fuddlesworth/pokebw2) | The engine: source for the whole ARM9 program, `res/` data packers, ROM rebuild | GPL-3.0 | `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c` (2026-10-31) | Matching decompilation of both US ROMs; every function in C; data as JSON + schemas, glTF, PNG and assembly; DSi-hybrid rebuild. No other Gen 5 base comes close. Integration: ADR 0002. |
| pokebw2's downloaded toolchain: wibo `pokebw2-sjis-1`, sjiswrap `v1.2.2-pokebw2.1`, dsd `v0.12.1-dsi.10`, objdiff `v3.8.1`, Metrowerks `mwccarm` | Compile, link, delink and rebuild | wibo (fuddlesworth fork) MIT; sjiswrap (fork) Apache-2.0; ds-decomp/dsd (fork) MIT; objdiff Apache-2.0; Metrowerks: proprietary, not redistributable | as pinned by upstream's `configure.py` | Upstream's matching build requires these exact versions. We cache them; we never redistribute the compilers (R-12). |
| Rust (rustup, stable) | Builds Kaleido's patched dsd (ADR 0004) until upstream takes the change | MIT / Apache-2.0 | stable at Phase 1 (1.99.1 in Phase 0) | dsd is Rust; the patch adds `--allow-stale-secure-area`. |
| Python 3.11+ | Kaleido's tooling (`framework/`) | PSF | In CI, 3.11 for the framework (the oldest supported) and 3.12 for the engine, as upstream's CI | Upstream's tooling is Python; one language for both. |
| ninja, LLVM (`clang`, `llvm-objcopy`) | Build graph, script assembly | ninja Apache-2.0; LLVM Apache-2.0 with LLVM exception | Ubuntu packages, versions recorded by `doctor` | Required by upstream. |
| [xdelta3](https://github.com/jmacd/xdelta) | Patches for players | Apache-2.0 | 3.0.11, Ubuntu's package (`sudo apt install xdelta3`) | The brief's distribution format. 3.0.11 predates 3.2's armor; with `-A` its patches don't depend on file names (`hardware-and-rom.md`). |
| clang-format 23.1.1 | Format engine C | Apache-2.0 with LLVM exception | 23.1.1 | Upstream pins it; our patches must pass upstream's style. |
| Ruff | Format and lint Kaleido's Python | MIT | 0.17.3 (`framework/requirements-ci.txt`, Dependabot updates it) | One tool for both jobs. |
| GitHub Actions: `actions/checkout`, `actions/setup-python`, `actions/cache` | CI | MIT | v7.0.1, v7.1.0, v6.1.0 by commit SHA (`.github/workflows/ci.yml`, Dependabot updates them) | GitHub's own actions; nothing else runs in CI. |
| melonDS (primary), DeSmuME (secondary) | Manual and scripted testing | melonDS GPL-3.0; DeSmuME GPL-2.0 | latest stable at Phase 1 | Brief default; see `hardware-and-rom.md` for DSi-mode support and scripting. |
| Blender | Map and prop authoring (glTF 2.0) | **Unverified** (GitHub reports `NOASSERTION`); an artist's tool, not a build dependency | artist's choice | Upstream's map pipeline is built around Blender exports. |

## Reference only (read for behavior and formats; never copy)

| Source | License | Use |
| --- | --- | --- |
| pret decomps: pokered, pokeyellow, pokecrystal, pokefirered, pokeemerald, pokediamond, pokeplatinum, pokeheartgold | none (all rights reserved) | Original game behavior, data layouts for our extractors, ROM SHA1s. A builder's local checkout may later be an optional extraction input; never committed. |
| ds-pokemon-hacking/White2Upgrade | none | How dex expansion and Fairy were done, and what broke (E5, Tier 2/3). |
| ds-pokemon-hacking/CTRMapV | none | Gen 5 map and zone format behavior; possible local inspection of built ROMs. |
| ds-pokemon-hacking/swan | GPL-3.0 | B2W2 symbols and struct layouts; pokebw2 already imports its names. |
| ds-pokemon-hacking/CTRMap-CE | GPL-3.0 | Nitro model handling reference (COLLADA/OBJ import, NSBMD writer in CTRMapV). Reusable under GPL if ever needed. |

## Exclude

| Tool | License | Reason |
| --- | --- | --- |
| PlatinumMaster/SwissArmyKnife | none | Binary ROM editor; dormant since 2023; no license. |
| FrostFalcon/FrostsGen5Editor | none | Binary ROM editor for Windows; no license; states it is incompatible with White2Upgrade. At most an inspection tool for built ROMs, never in the pipeline. |
| ds-pokemon-hacking/PMC (+ libRPM, RPMAuthoringTools) | GPL-3.0 (libRPM/RPMAuthoringTools: none) | Code injection into a built ROM; redundant when the source is available. |
| CTRMap-CE / CTRMapV as a build step | GPL-3.0 / none | Works on ROMs or extracted files, project files of its own, no glTF; its Gen 5 half is unlicensed. |
| devkitPro ndstool | GPL-3.0 | Not needed: upstream's dsd builds the ROM, including DSi-hybrid parts. |

## Candidates, not adopted yet

| Tool | License | When it might be needed |
| --- | --- | --- |
| RoadrunnerWMC/ndspy | GPL-3.0 | Reading NARC/NDS structures outside upstream's tools (e.g. ROM validation, extraction tests). Add only if upstream's own `tools/data/narc.py` and friends don't cover it. |
| Garhoogin/NitroPaint | BSD-2-Clause | An artist's editor for Nitro textures and 2D graphics. A dev tool, not a dependency. |
| A glTF → Nitro encoder for new map models and texture sets | to be written (GPL-3.0) | Required if E4b confirms R-01; offered upstream first. |

## Rules that follow from this

- Kaleido's repository depends only on GPL-compatible code. Unlicensed projects are read, never copied (AGENTS.md).
- Each tool's version and hash is recorded where `doctor` can check it. New dependencies need a reason in the PR that
  adds them.
