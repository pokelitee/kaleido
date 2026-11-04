# E10 — Regenerate `res/` from a ROM

Phase 0 experiment (`docs/plan/05-roadmap.md`), run 2026-11-03 on the owner's machine in a scratch worktree
`~/kaleido-work/e10-res` of pokebw2 at `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c`, with the owner's Black 2 ROM
(SHA1-checked in E0). Question: if upstream became unavailable (R-03), could `res/`, its ~140k extracted files, be
rebuilt from a player's ROM with upstream's own dumpers?

## Summary

- **Mostly yes, with gaps.** From an emptied `res/` (the 84 hand-written schemas kept), upstream's dumpers rebuilt
  104,424 of the 139,732 files (74.7%) from the Black 2 ROM in a few minutes. All but 88 match upstream's in content,
  and every rebuilt archive packs back to Black 2 byte for byte. **Verified**: the full matching build passes with SHA1 `e51e6dfb8678a3d19dcd2a10691b96a569ca0abb` (§3).
- **The gaps**:
  - 13.1% needs a White 2 ROM: the dumpers of the 2D graphics, the Pokédex, encounters and the town map read both
    versions.
  - 12.1% needs Apicula, an external model converter: map and field prop models.
  - 88 files (74 text, 14 trainer AI scripts) carry upstream's own curation, which no dump reproduces.
- **So the bootstrap can't rely on regenerating `res/` alone.** An owner-controlled mirror (ADR 0002) is still needed.
  Regenerating from ROMs is a fallback that also needs a White 2 ROM, Apicula, and upstream's message labels kept
  apart from the text (§4).
- Upstream has two stale output paths in `list_text_data.py`, and the build hit R-28 again (§2).

## 1. How `res/` is made

**Verified** in pokebw2's `docs/data.md` and tools at the pin:

- Every archive built from `res/` has a script that "wrote its sources from the original" and can write them again.
  About 80 dumpers exist, each with its own `dump`/`extract`/`disasm`/`unpack` command; there is no driver for all of
  them.
- File and directory names come from the constant lists in `generated/`, which are upstream's own (curated names, some
  bootstrapped once by `make_constants.py`). E10 keeps `generated/` as it is.
- Map and prop models go through Apicula (`map_model_data.py extract APICULA …`); upstream doesn't pin a version.
- The graphics archives' dumper (`graphics_archive.py`) reads Black 2's and White 2's files and writes `black2/` and
  `white2/` for members that differ. It needs both ROMs even where nothing differs.

## 2. The run

A driver ran every documented dumper that needs nothing beyond the checkout, in dependency order (species before the
sprites and cries, text before the dumpers that read text). Time: 112 s, plus a second pass for the dumpers that
read text. Compared with the committed `res/` through git:

| Files | Result |
| --- | --- |
| 94,517 | Rebuilt identical. 390 of them land in the wrong place (below) |
| 9,819 | Rebuilt with different bytes, same content. 4,741 indexed PNGs have the same palette indices and palette; 5,078 texture PNGs have the same RGBA pixels |
| 88 | Rebuilt, but not as upstream keeps them (§2.1) |
| 18,346 | Not rebuilt: need White 2. Graphics, demo, gimmick, effect, particle, font and sound archives 17,415; Pokédex 710; encounters 135; town map 86 |
| 16,962 | Not rebuilt: need Apicula. Field prop models 12,662; map models 4,300 |
| **139,732** | |

- `list_text_data.py` writes places to `res/places/` and trainer classes to `res/trainer_classes/`. Upstream keeps
  them in `res/field/places/` and `res/trainers/classes/`. All 390 files equal upstream's.
- Field scripts (1,289 files) rebuilt identical.

### 2.1 The curated files

- **74 text files**: upstream renamed messages that the C code uses (`BtlMain12_Text_Slash` where the dump writes
  `BtlMain12_Text_Empty`). It also moved names and Pokédex text into the species, item and other JSON files, which the
  text pulls in with `\from{…}`. The dumped text compiles without those labels: the first build failed on undefined
  identifiers in `print_msg.c` and `pms_input_data.c`. Packed as dumped, the system text archive `a/0/0/2` also
  didn't match; the cause wasn't traced (**Unverified**).
- **14 trainer AI scripts**: upstream "edited by hand since" the disassembly (`tr_ai_script.py`). What changed wasn't
  examined.

## 3. The build from regenerated sources

In the worktree:

- every rebuilt file kept, including the 9,819 with different bytes;
- the 88 curated files put back from upstream;
- the files that couldn't be rebuilt put back from upstream;
- `configure.py b2_us && ninja` until nothing was left to compile.

**Verified**: every matching check passed, SHA1 `e51e6dfb…`. Every archive packed from rebuilt sources equals Black
2's. Two ninja runs were needed (R-28).

## 4. What this means for R-03

If upstream's repository disappeared, Kaleido would still have its pinned copy of upstream's code, tools,
`generated/` and schemas: the mirror or a local clone. Rebuilding `res/` from a player's ROMs then needs:

| Need | Status |
| --- | --- |
| Black 2 ROM | the player's base ROM, required anyway |
| White 2 ROM | required for 13% of files, although Kaleido builds only Black 2. A dumper change could fall back to Black 2's files where the versions don't differ (**Assumption**) |
| Apicula | an external tool, not installed or tested here; license and version **Unverified** |
| Upstream's message labels and `\from` layout | kept only in upstream's text files, which also hold the game's text. A label list (names only) applied to dumped text would separate the two (**Assumption**) |
| Upstream's AI script edits | 14 files; not examined |

Regeneration is therefore a fallback, not a replacement for the mirror. Phase 1 sets up the mirror (ADR 0002) and
keeps this experiment's driver as a recovery test.

## Not done

- The White 2 and Apicula parts. They need the owner's White 2 dump and, for Apicula, a download and build of
  third-party code.
- Tracing why the dumped system text packs differently, and what the AI script edits are.
- Upstream fixes for the two stale output paths in `list_text_data.py` (not offered).

The worktree `~/kaleido-work/e10-res` holds the regenerated tree and its build; it's scratch.
