# Glossary

| Term | Meaning |
| --- | --- |
| ADR | Architecture Decision Record, in `docs/decisions/` (ADR 0001). |
| Approximate | Fidelity class: the feature exists but differs from the original; the difference and reason are stated. |
| ARM9 / ARM7 | The DS's two CPUs. pokebw2 decompiles the ARM9 program; the ARM7 program is taken unchanged from the base ROM. |
| ARM9i / ARM7i | The DSi-only programs in a DSi-hybrid ROM's TWL region. |
| Base ROM | The player's Black 2 (USA/Europe) dump that a Kaleido patch applies to; SHA1 `e51e6dfb…`. |
| Baseline | The patched engine built with every Kaleido define off and no content layers. It must match Black 2's SHA1. |
| Category (provenance) | One of: 1 upstream, 2 extracted, 3 original, 4 third-party (`docs/plan/03-architecture.md` §6). |
| Constant list | A file in pokebw2's `generated/` (`zones.txt`, `species.txt`, …) whose lines define IDs in order. |
| dsd | `ds-decomp`, the tool that delinks the ROM and rebuilds it; pokebw2 uses a DSi-hybrid fork. |
| DS mode / DSi mode | How a hybrid ROM runs: DS mode on any DS (4 MB RAM), DSi mode on DSi/3DS (more RAM, TWL features). |
| Exact | Fidelity class: behaves as the original. |
| Extraction | Reading other-game content from the builder's own ROM at build time, SHA1-gated; output is never committed. |
| Family | A set of games with one story (FRLG, RBY). Sits between region and game in the hierarchy. |
| Hybrid ROM | An NDS ROM with a DSi (TWL) region, digests and signatures. Black 2 is one. |
| Infeasible | Fidelity class: can't be done on this engine or hardware; the reason is stated. |
| Layer | A directory of content shaped like pokebw2's tree, merged in hierarchy order (region → family → game). |
| LTD module | The DSi-only code module in ARM9i, loaded at `0x02700000` in DSi mode. |
| Matching build | A build that reproduces the original ROM byte for byte. |
| Merge patch | An RFC 7396 JSON Merge Patch file (`*.merge.json`) that edits a lower layer's JSON file. |
| Modcrypt | AES-CTR encryption of part of a DSi-hybrid ROM (ARM9i's first 0x4000 bytes in Black 2). |
| MWCC | Metrowerks CodeWarrior C compiler, the game's original compiler, run through wibo. |
| NARC | Nitro archive: numbered files under `files/a/…` in the ROM. |
| Nitro (NSBMD, NSBTX, …) | Nintendo's DS 3D model and texture formats. |
| Overlay | Code loaded into a fixed memory region on demand; Black 2 has 344. |
| Ruleset | A per-game choice of compile-time engine variants and merge-time data transforms (`gen3`, `gen1`). |
| Region | Shared geography and location IDs used by several families (Kanto). |
| `res/` | pokebw2's editable game data: JSON, glTF, PNG, WAV, assembly scripts. |
| Shift build | A pokebw2 build with code padded (`--shift`) to prove that size changes don't break pointers. |
| Zone | A map area with its header (`res/field/zones/`), events and scripts. |
