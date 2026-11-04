# 08 — Phase 3 plan: Pallet Town to Viridian City

Status: **proposal** for owner review (2026-11-04). It expands the roadmap's Phase 3 (`05-roadmap.md`) into work,
order and decisions. It estimates sizes, not time: measuring time is one of Phase 3's exits.

## Goal

From the roadmap:
- **Scope:**
  - places: Pallet Town, Route 1, Viridian City (Pokémon Center, Mart), Oak's Lab, the player's house;
  - NPCs and signs, with dialogue extracted from FireRed;
  - wild encounters, at least one trainer, and the Oak's Parcel progression;
  - a new game that starts in Pallet Town;
  - the first switches for the B2W2 systems on this path, with FireRed's config choosing each.
- **Exit:**
  - playable in melonDS from New Game to delivering Oak's Parcel;
  - validation clean, and provenance covering every file;
  - art cost per map recorded.

Music: Q6 asks for one FRLG song converted in Phase 3, then a decision (R-24).

## What the path holds

The maps in scope, about nine:
- Pallet Town;
- the player's house (two floors);
- the rival's house;
- Oak's Lab;
- Route 1;
- Viridian City;
- Viridian's Pokémon Center;
- Viridian's Mart.

The story beats below are what the original game does (**Assumption**, from the original game; W2 confirms each
from the builder's ROM before scripts are written):
- Oak stops the player at the edge of town and leads them to the lab.
- The player chooses a starter, and the rival chooses the one strong against it.
- The rival battles the player in the lab: the "at least one trainer", since Route 1 has none.
- A Mart employee on Route 1 hands out a sample Potion.
- Viridian's Mart clerk gives the player Oak's Parcel.
- Delivering it earns the Pokédex and Poké Balls.
- An old man blocks Viridian's north exit until then.
- The rival's sister gives the Town Map.

## Workstreams

| # | Workstream | What | Size |
| --- | --- | --- | --- |
| W1 | Zones and maps | Map each location to an existing zone of a fitting map type (ADR 0004), in `regions/kanto/zones.json`, and pick zones whose IDs the code doesn't treat specially. Lay out events (warps, NPCs, signs, triggers) per zone. The map art follows decision D1 | M (stand-ins) / L (new maps) |
| W2 | Extraction | New recipe kinds on the builder's FireRed: each map's events (NPC positions and sprites, warps, signs), its dialogue (the messages its scripts show, converted from Gen 3's text encoding and control codes to Gen 5's), trainers and parties (the rival's three), and items on the ground. Route 1's encounters exist (E8) | L |
| W3 | Scripts | Hand-written in pokebw2's script assembly (category 3), one file per zone, using the extracted text by label and B2W2's free flag and variable ranges: the beats above, plus the Pokémon Center's healing and the Mart, from B2W2's generic scripts where they fit | L |
| W4 | Start, intro and items | A new game that starts in the player's room in Pallet Town, past Black 2's opening (where Black 2 sets its start is still to find). Oak's intro speech, with his look per D3. Oak's Parcel as B2W2's existing `ITEM_PARCEL` renamed, if its key-item behavior fits (an experiment), and the Town Map, which exists | M |
| W5 | B2W2-system switches | For FireRed, per D5: seasons, Pass Powers, the Unova Pokédex (a Kanto Pokédex of 151, which E5 found is data) and the C-Gear (switch exists, patch `0006`). Each a `KALEIDO_NO_*` define like the C-Gear's, traced first (`docs/research/b2w2-systems.md`) | M |
| W6 | Map art (ADR 0003) | Template-append as an engine patch (recorded from E4b). Kaleido layers carry map models and texture sets. Validation checks each chunk against its map type's `chunkBufferSize`. Then the maps D1 asks for, with time logged per map | M (tooling) + per map |
| W7 | Music prototype | Convert one FRLG song (Pallet Town's) from the builder's ROM to Nitro's sequence format at build time, using B2W2's instrument banks, then decide (Q6) | M–L |
| W8 | Checks and records | Validation for what Phase 3 adds: scripts name existing text labels, flags and variables stay in the free ranges, events' zones and warps. Provenance for every new file. The art-cost log, the encoder's scope (ADR 0003 asks for it at the end of Phase 3), and fidelity notes | S–M |

## Order

1. **A walkable Kanto skeleton** (W1, W4's start): a new game starts in the player's room in Pallet Town. Warps
   join the nine locations, on stand-in maps if D1 says so. Nothing to read yet, but the shape is testable early.
2. **Content from the ROM** (W2): events and dialogue land in the skeleton, NPCs stand where FireRed puts them, and
   signs read FireRed's text.
3. **The story** (W3, W4's items): Oak's escort, the starter, the rival battle, the Parcel errand and the Pokédex,
   playable end to end. **This meets the main exit.**
4. **Systems** (W5), alongside 2 and 3: FireRed's switches, and the Kanto Pokédex the story hands out.
5. **Art** (W6): template-append, then Pallet Town (and Route 1 if time allows) as new maps, timed. **This meets the
   art-cost exit** and writes the encoder's scope.
6. **Music** (W7), in parallel from step 2: one converted song, then the Q6 decision.

Each step lands as its own pull requests, with `kaleido build firered` and `validate` clean.

## Decisions for the owner

| # | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| D1 | **Maps for the prototype** | (a) Kanto's story on existing Unova maps first, as stand-ins, then replace them with new maps one at a time; (b) new Kanto maps before the story; (c) a converter that turns FRLG layouts from the builder's ROM into Gen 5 chunks automatically (extracted content, a large tooling bet) | (a), with Pallet Town (and Route 1 if possible) rebuilt as new maps for the art-cost measurement; (c) only as a spike if art turns out to be the bottleneck |
| D2 | **Who makes map art** | The owner or artists, in Blender against template materials; or simple generated geometry from Kaleido's tooling, as placeholders | Owner or artist for the measured maps (the measurement is of real art); generated placeholders only where a map just needs to exist |
| D3 | **Professor Oak's look** | Juniper's sprite as a placeholder with Oak's words; original Oak art (CC BY-SA) now | Placeholder in Phase 3; Oak's art with the other trainer art later |
| D4 | **The player character** | B2W2's Nate and Rosa; new Kanto player art | Nate and Rosa (Approximate) until art is scheduled |
| D5 | **FireRed's B2W2 switches on this path** | Per system: keep or switch off (C-Gear, seasons, Pass Powers, Unova Pokédex). FRLG had none of them, but had a wireless adapter | Off for seasons, Pass Powers and the Unova Pokédex (Kanto Pokédex instead). For the C-Gear, the owner's call |
| D6 | **Encounter rates** (`01-feasibility.md` says Phase 3 decides the rule) | Every FRLG land rate to one Gen 5 setting (E8's 7); a mapping from FRLG's rate to the nearest setting; per-map hand tuning | A mapping, written once and recorded as Approximate |

## Risks for this phase

- **R-01, map art.** D1 (a) keeps the story off the critical path of art.
- **R-05, RAM.** The field has 110,696 B of heap 1 free (E6b). New scripts and text cost little; new map models live
  in the field heap and have per-chunk limits (W6 checks them).
- **Text fit.** E1's glyph and long-line details are still pending (playtest list). W2's converter reflows text to
  Gen 5's boxes, and checks the result.
- **Script work** is the largest hand-written cost. B2W2's generic scripts (healing, Mart) are reused where they fit.
- **Automated checks wait.** The owner set harness testing aside, so playthroughs are manual (the playtest pass) until
  it resumes. Black 2's route showed the harness can drive story scenes.

## Not in Phase 3

- Route 2, Viridian Forest, Pewter City and Brock (Phase 3.5).
- Route 22 and its optional rival battle.
- The Viridian Gym.
- Hardware and the DS Protect guard (Phase 3.5 and E7).
- The Nitro encoder (Phase 3.5 to 4).
- LeafGreen (Phase 4).
