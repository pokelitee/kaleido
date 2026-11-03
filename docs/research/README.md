# Research

Findings that plans and decisions rest on. Every finding is tagged:

- **Verified**: read in the source named, with a commit or date.
- **Unverified**: not confirmed; don't build on it without checking.
- **Assumption**: our inference, with the experiment that will test it.

| Note | Covers |
| --- | --- |
| [pokebw2.md](pokebw2.md) | The engine: build, completeness, DSi handling, data formats and their limits, battle code, save, reusable art |
| [peripheral-tools.md](peripheral-tools.md) | White2Upgrade's expansion findings, CTRMap, editors, pret decomps, licensed tooling |
| [hardware-and-rom.md](hardware-and-rom.md) | DS/DSi limits, the Black 2 cart and ROM, hybrid boot paths, emulators, xdelta, source ROM hashes |
| [e0-baseline.md](e0-baseline.md) | Phase 0 E0: baseline build. E0a (no-ROM compile) and E0 (matching build, twice from clean) both passed |
| [e4b-map-art.md](e4b-map-art.md) | Phase 0 E4b: new map art. Upstream refuses it; a template-append prototype ([patch](e4b-template-append.patch)) builds and plays normally in melonDS; chunk size budgets |

Each Phase 0 experiment adds its own `e<N>-<topic>.md` here.

## Section 3 baseline, re-verified 2026-11-03

The brief's Section 3 baseline, checked item by item. Corrections are in bold.

| Brief's claim | Status | Detail |
| --- | --- | --- |
| pokebw2: matching decomp, both US ROMs byte for byte | Verified | `41f42ca`; ByteMatch 100% code, 43,418/43,418 functions, 1,792/1,800 units |
| Every ARM9 main and overlay function in C, one asm exception | Verified | `docs/nonmatching-functions.md` |
| ARM7 handling not yet reviewed | Verified, now reviewed | **ARM7 is not decompiled**; it passes through from the base ROM |
| GPL-3.0; Python 3.11+, ninja, LLVM; `configure.py` downloads tools | Verified | Tool versions in `pokebw2.md` |
| `--bugfix`, `--shift` modified builds | Verified | Shift safety audited upstream |
| Game data editable in `res/` (JSON + schemas, glTF, PNG, palettes, WAV, asm) | Verified, **with a limit** | **New map models and texture sets can't be added** with today's packers |
| ~140k extracted Nintendo assets committed | Verified | 139,732 files |
| Hundreds of commits per day, mostly one maintainer plus agents | **Partly wrong** | 13–236 per day (median 105) in late October; **several contributors** |
| Ships `CLAUDE.md`, `AGENTS.md`, skills, hooks | Verified | Plus Codex copies |
| Long-term goal is a PC port | Verified | README |
| White2Upgrade: dex 721, Fairy, no license, last commit May 2025 | Verified | `main` 2025-05-05; a `dev` branch moved on 2026-06-04 |
| SwissArmyKnife: no license, last commit May 2023 | Verified | Default branch 2023-05-22; another branch 2023-11-04 |
| FrostsGen5Editor: active, no license, incompatible with White2Upgrade | Verified | v6.0.0 on 2026-10-27 |
| CTRMap-CE: GPL-3.0, active in 2026 | Verified, **with a catch** | **Its Gen 5 plug-in, CTRMapV, has no license** |
| pret decomps: active, no license files | Verified | All eight; HEADs in `peripheral-tools.md` |
| Still to research: ByteMatch page | Done | `hardware-and-rom.md` |
| Still to research: White2Upgrade expansion limits | Done | `peripheral-tools.md` |
| Still to research: ROM and save size limits | Done | 512 MB cart (melonDS refuses more); 512 KB FLASH save **behind an infrared port** |
| Still to research: RAM and overlay headroom | Bounds known, headroom not | 4 MB DS / 16 MB DSi; ARM9 ≤ 2.5 MB on DSi even in DS mode; headroom needs E6 |
| Still to research: DSi-hybrid validity of modified builds | Partly | Build recomputes HMACs and modcrypt; RSA can't be redone; boot paths need E7 |
