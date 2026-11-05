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
| [e6-headroom.md](e6-headroom.md) | Phase 0 E6: ROM ≈ 231 MiB free; ARM9 far under the DSi limit; DS-mode RAM ≈ 213 KiB for added code and static data; E6b (runtime) moved to Phase 1's harness spike |
| [e1-e3.md](e1-e3.md) | Phase 0 E1–E3: text, trainer data and a battle code switch (`--define`, [patch](e3-define.patch)); built-ROM checks pass; in-game rival battle pending |
| [e4a-new-zone.md](e4a-new-zone.md) | Phase 0 E4a: a new zone's data packs ([patch](e4a-extra-zones.patch) for the "no zone" collisions); ARM9 main changes need the DS ARM7 BIOS (R-27), solved by a dsd flag ([patch](dsd-allow-stale-secure-area.patch), ADR 0004) |
| [e5-species.md](e5-species.md) | Phase 0 E5: species #650 builds into every archive after a matching-neutral [patch](e5-species-expansion.patch) derives the species-count numbers and lets two packers splice in a template's files; capacity 672 for the Pokédex save; known gaps |
| [e8-extract-encounters.md](e8-extract-encounters.md) | Phase 0 E8: our extractor ([prototype](e8-frlg-wild.py)) reads FireRed Route 1's wild encounters from the owner's SHA1-checked ROM by structure, deterministically, into an encounter table that packs into Black 2 |
| [e9-save-identity.md](e9-save-identity.md) | Phase 0 E9: a per-game save magic ([patch](e9-save-magic.patch)) makes another game's card, B2's included, read as empty; header and save type unchanged; any ARM9 main change can touch the secure area |
| [e10-regenerate-res.md](e10-regenerate-res.md) | Phase 0 E10: upstream's dumpers rebuild 74.7% of `res/` from a Black 2 ROM, build-equivalent; the rest needs White 2, Apicula and upstream's curated labels, so the mirror stays the plan |

| [frlg-dialogue.md](frlg-dialogue.md) | Phase 3 W2: the path's 174 messages read from FireRed's map scripts by structure, converted to Gen 5 text (breaks, names, fonts) and appended to the stand-ins' banks; no reflow needed |

| [frlg-trainers.md](frlg-trainers.md) | Phase 3 W2: FireRed's trainers, parties and prize money found by structure; the rival's three lab parties on Black 2's first rival battles, with IVs and prize carried over exactly |

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
