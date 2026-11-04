# E8 — Extract a FireRed table

Phase 0 experiment (`docs/plan/05-roadmap.md`), run 2026-11-04 on the owner's machine. Question: can a FireRed table be
read from the owner's ROM into pokebw2's `res/` format, deterministically, with nothing ROM-derived committed (R-10)?

## Summary

- **Yes, for Route 1's wild encounters.** [`e8-frlg-wild.py`](e8-frlg-wild.py), our own code, reads the owner's
  FireRed and writes a `res/field/encounters/` table. It finds everything by structure and names the map by the ROM's
  own text. Two runs give byte-identical output, and its 12 slots equal pret's FireRed Route 1. **Verified** (§2).
- **The source ROM**: the owner's dump is FireRed (USA), SHA1 `41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc` (game code
  `BPRE`, revision 0), the hash recorded from pret's README. It is the first extraction target (Q5). The extractor
  refuses any other ROM.
- **Shown on Route 19, not on E4a's zone**: E4a's zone is a house without grass, and ADR 0004 has Kanto reuse
  existing zones. Route 19 (Aspertia's first route) took the extracted table. The ROM builds without
  `--allow-stale-secure-area`, since only data changed, and the table reads back from the built archive. **Verified**.
- **The encounter rate doesn't carry over.** Gen 5 has no per-step rate, so FireRed's rate becomes a Gen 5 ramp setting
  (Approximate, §3).
- Committed: the extractor and this note. Not committed: the ROM, the extracted table and the test ROM.

## 1. Finding the table

The formats come from reading pret/pokefirered at `ce6406d8`; the extractor's docstring lists them. Nothing was
copied. The extractor:

1. checks the ROM's SHA1;
2. encodes the map's name ("ROUTE 1") in the game's text encoding, finds it in the ROM, and finds the table of
   pointers to section names that points at it. The table's index plus `KANTO_MAPSEC_START` (0x58, counted from
   pret's section list) is the map section;
3. finds the map headers in that section, then their place in the map groups' tables: map group and number;
4. finds the wild encounter headers by their shape (the longest run of 20-byte entries ended by 0xFF 0xFF), and the
   entry for that map;
5. reads its 12 land slots and converts species 1–251, which are in national order (**Verified**, pret's species
   constants), to pokebw2's `SPECIES_*` names. Anything above 251 stops the run: reading the ROM's national-order
   table is Phase 1's job.

**Verified** results, all derived from the ROM:

| Step | Result |
| --- | --- |
| Map section | `0x65` (pret's `MAPSEC_ROUTE_1` is the same) |
| Map | group 3, number 19 |
| Wild encounter headers | at ROM offset `0x3c9cb8`; Route 1 is entry 87 |
| Land slots | 12, all species in national order |

## 2. Checks

| Check | Result |
| --- | --- |
| Determinism | two runs, byte-identical output, SHA-256 `488c6a6c12a7feabc0fff12a871a994bb92bdd67870a6157e88a1303c5b421d6`; about 5 s each |
| Against pret | all 12 slots (species, minimum and maximum level) equal pret's FireRed Route 1 land table, and so does the land rate. Read in a scratch copy, nothing kept |
| Packs into Black 2's archive | branch `phase0-e8` at the pin, `route_19.json` replaced by the output, ROM target. The built `a/1/2/7` entry 128 (`ENCOUNTERS_ROUTE_19`) is 232 bytes like the original, with grass setting 7, the 12 grass slots equal to the extracted table (form 0), and every other rate and slot empty. `verify_dsi_rom.py` passes. Test ROM `~/kaleido-work/e8/kaleido-e8-test.nds`, SHA1 `cc4f38a58b6c11620b066bc86a325d9dff16fe7e`, never committed. The scratch branch is local and never pushed |

## 3. Mapping onto Gen 5

| FireRed | Black 2 | Class |
| --- | --- | --- |
| 12 land slots | 12 grass slots, in order. The slot odds are the same (`01-feasibility.md`) | Exact |
| Land encounter rate, a per-step chance | A walking group's rate is one of 12 settings of a per-step ramp (`ENCOUNT_RATE_CONFIGS`, `field_encount.c`). Any land rate becomes setting 7, the most common in Black 2's grass tables (88 tables and seasons); the original rate is reported, not carried over | Approximate (by decision: Gen 5 decides how things work) |
| Water, Rock Smash and fishing groups | Not part of E8. Water has 5 slots in both games; Rock Smash has no Gen 5 equivalent; FireRed's three rods map onto Black 2's one | Phase 3 |
| Seasons, shaking grass, dark grass | Empty, rate 0: Kanto has none (Q7) | — |

## 4. What Phase 1 takes from this

- A recipe names a map by its text and a table kind. The extractor resolves the locations, so recipes need no offsets.
  `03-architecture.md` §6 allows offsets; this shows they aren't needed for this table.
- Species past 251 need the ROM's own national-order table.
- The writer should use pokebw2's JSON formatting, so that extracted files diff cleanly against upstream's.

## Later

- Phase 1 turned the prototype into `framework/extractors/gba_gen3.py`. Its unit tests found a flaw in the header
  scan, which the prototype has too. After a run of header-shaped entries without the terminator, the scan went on
  from the run's end. That can skip a real table starting inside the false run. On the owner's ROM the scan still
  found the right table, so the results above stand. The framework's version goes on from the next word instead.
- Phase 3 (2026-11-04) found a second flaw, in naming a map's section. The lookup took the longest run of pointers
  that holds the name. The owner's FireRed also has a longer run of the same names, in another order (**Verified**:
  109 and 174 names, both starting with Pallet Town). So 35 of the 109 names gave the wrong section. Route 1's came
  out right (`0x65`), so the results above stand.

  The framework now finds the table of section names by its shape, the one run of exactly 109 names, a name per
  section from `0x58` to `MAPSEC_NONE`, and looks names up in it. That run gives Pallet Town at `0x58`, Viridian City
  at `0x59` and Route 1 at `0x65`.

## Not done

- In-game check: walk Route 19's grass in the test ROM and meet FireRed Route 1's species at its levels. Deferred to
  the playtest pass (`docs/status.md`).
- LeafGreen, other maps, and the other encounter groups.
