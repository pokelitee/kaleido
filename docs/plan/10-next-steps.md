# 10 — Plan: from the spike to Phase 3's exit, then Brock

Status: **proposed** (2026-11-08). It orders the work left in Phase 3 (`08-phase3.md`, `09-generated-maps.md`) and
outlines Phase 3.5 (`05-roadmap.md`). Owner's answers so far (2026-11-08):
- the emulator harness comes back, to run the deferred playtest checks;
- the plan covers Phase 3's exit in detail and Phase 3.5 in outline.

It estimates sizes, not time.

## Where things stand

- Phase 3's story, through the Parcel, is built on Unova stand-ins (steps 1 to 4). Nothing of it has been seen in game:
  14 rows wait under "Deferred to playtesting" in `docs/status.md`.
- Generated maps: template-append and the chunk check are in (step 1), and the textured Pallet Town spike is built
  (step 2, `022bd2c9…`). Step 3, the Kanto matrix, waits on the owner's verdict on the spike.
- Phase 3's exit also asks for one FRLG song converted (Q6, R-24) and the art cost per map recorded. Neither has
  started.

### The spike in the harness (2026-11-08)

The textured spike ran in py-desmume through the harness prototype (`docs/research/e6b-harness.py`), from power-on
through the intro to Pallet Town, and walked around the town. The screenshots stay on the builder's machine, since
emulator screenshots are never committed. **Verified**, from those screenshots:
- **Reads as intended:** the forest border along the north, the flower bed behind its standing picket fence, the signs
  and the mailbox. Black 2's buildings stand on FireRed's houses and lab, and the paths' edges blend.
- **Reads off:**
  - almost all the ground shows as sand path, with grass only around the flower bed;
  - Black 2's buildings look large for FireRed's grid, as §7 of `generated-maps-spike.md` measured;
  - the pond wasn't reached.
- **Not seen:** the player's sprite. It shows in none of the field screenshots, although the view moves when the player
  walks and stops at buildings.

**Unverified**: whether the player is missing from the ROM or only from the harness's screenshots. The stand-in
FireRed build, run the same way for comparison, stayed in name entry, because its intro takes other presses. Also
**Unverified**: whether FireRed's own Pallet Town has more path than grass. The labels weren't compared tile by tile.

## Decisions for the owner

| # | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| D11 | **The spike's verdict** (`09-generated-maps.md`, step 2) | (a) go on to the Kanto matrix with touch-ups; (b) a second polish pass before more maps; (c) rethink the source of Kanto's maps | (b), small: settle the player sprite, the grass/path split and the building fit (step B), then (a) |
| D12 | **Where Kanto's matrix goes** (`09-generated-maps.md`, unknowns) | (a) an unused corner of Unova's overworld matrix; (b) a matrix of its own with its own zones | (a) for Phase 3, since it needs no engine work. Read the matrix loader before Phase 3.5's maps |
| D13 | **A device** (E7) | Buy one now; at Phase 3.5's start; at its exit | At Phase 3.5's start: its exit is the latest point (Q4), and a save on hardware is one of its checks |
| D14 | **Release channel** (R-06) | Decide now; at the first release | At the first release, as the roadmap says; nothing in this plan publishes a patch |

## Order

Each step lands as its own pull requests, validated and built, with `docs/status.md` updated.

### A. Housekeeping (small; before step D)

1. **Map-model recipes that share a matrix.**
   - Today each `gba_gen3_map_model` recipe writes `generated/map_models.txt` and a merge patch of the whole matrix,
     read from upstream (`framework/kaleido/extract.py`).
   - A second recipe in the same layer is refused, since it writes the same paths. A lower layer's matrix edits would
     also be lost, since a merge patch replaces the whole `maps` grid.
   - Fix: one recipe takes a list of maps for one matrix, or `extract` combines the outputs. Either way, test it with
     two maps in one matrix.
2. **The ROM-content guard** (`framework/kaleido/check.py`) also refuses:
   - Nitro archives and files by their magic (`NARC`, `BMD0`, `BTX0`);
   - a ROM's file names (`arm9.bin`, `arm7.bin`, `header.bin`, `y9.bin`, `banner.bin`) and paths under `overlay/`;
   - the other patch formats (`.bps`, `.ips`, `.ups`).
3. **The story's flags and variables:** `validate` checks that no Black 2 script in the merged tree uses
   `frlg_story.inc`'s range (from 0x1F2 and 0x404E). Today this is an **Assumption** from a one-time scan.

### B. The harness as a command (ADR 0005)

The prototype found its route by frame counts, one savestate at a time, and any build that shifts a frame breaks it
(`harness-spike.md`). For the deferred checks to keep running as content changes, the harness has to wait on the
game's state, not on frames.

1. **`./kaleido play <game> <route>`**, in `framework/`, on the builder's machine only, never in CI.
   - py-desmume, with steps as in `e6b-route.txt`.
   - Outputs (screenshots, savestates) go to `build/<game>/play/`.
2. **State, read through pokebw2's symbols:**
   - the zone ID and the player's position;
   - whether a script or text box is running;
   - the battle state;
   - flags and variables.

   Each step waits for a state ("until zone ZONE_ROUTE_19", "until no script"), with a timeout that fails the run.
   The addresses come from the game's own symbols for its build.
3. **Routes** under `content/games/<game>/play/`. They are original (only button presses and checks), so they can be
   committed.
4. **First routes**, in this order:
   - the spike: is the player's sprite drawn? (D11);
   - Phase 3 step 1: a new game's walk to Viridian;
   - 3a and 3b: each story beat, checked by its flag and variable, and by the party and bag in RAM;
   - E9 and Phase 2's save refusal: export and import a save;
   - Phase 2's C-Gear byte.
5. **What stays manual:** the look (the owner judges screenshots and plays once per milestone), text layout, sound,
   and DSi mode in melonDS.

A row moves out of "Deferred to playtesting" when its route passes. A route that fails is a bug, fixed before step D.

### C. The spike's touch-ups (D11 (b))

- **The player's sprite**, once step B settles where the fault is.
- **Grass and path:** compare the labels with FireRed's own tiles, and draw grass where FireRed has grass.
- **Buildings:** fit Black 2's houses and lab closer to FireRed's footprints, or record the difference as
  Approximate.
- **The pond and the map's name** (Aspertia City's today).

The owner then plays the spike once and confirms D11.

### D. The Kanto matrix (`09-generated-maps.md`, step 3)

- Pallet Town, Route 1 and Viridian City generated and joined in one matrix (D12).
- Their zones carry FireRed's events, warps and people at FireRed's coordinates. The story's scripts move from the
  stand-ins to those maps. Oak's walk returns (D7).
- The chunk check covers every new chunk. Place names come from FireRed (`place_names`).
- Harness routes from step B are rerun on the new maps, with new positions.

### E. Interiors (`09-generated-maps.md`, step 4)

- The two houses, the lab, the Mart and the Pokémon Center, generated the same way.
- Black 2's generic Center and Mart are the fallback where they fit better.

### F. Phase 3's exit

- **The playthrough:** from New Game to delivering the Parcel on generated maps, run by the harness, then played once
  by the owner in melonDS, DS mode.
- **Validation:** clean, with provenance for every file.
- **Art cost per map,** from steps C to E.
- **One FRLG song:** converted, and its decision recorded (R-24).
- `docs/status.md` and `05-roadmap.md`'s workload section rewritten with what was measured.

### Beside the steps

These don't block A to F and can run in their own sessions:
- **The Pokédex's area pages,** generated from the merged encounter tables. Run on Black 2's own tables, the generator
  must give back Black 2's area data (proposed 2026-11-08).
- **Item extraction:** FireRed's item balls, hidden items and Mart lists, needed by Phase 3.5. `validate` then checks
  each item event:
  - its flag is unique;
  - its object is an item ball;
  - it gives the item extracted for it.
- **Save layout:** once a release is out, the story's flags and variables never move, as save magics don't. This is
  written into `content/README.md` before the first release.

## Phase 3.5, in outline: through Pewter City and Brock

Scope, from the roadmap: Route 2, Viridian Forest, Pewter City, its Gym and Brock (badge, TM, gym trainers' AI), the
Center and Mart, Mt. Moon 1F, and a save and load.

| Need | Builds on | New work |
| --- | --- | --- |
| Maps | Steps D and E | A forest and a cave: new kits from Black 2 templates (Pinwheel Forest, a cave) and new labels for FireRed's tilesets |
| Wild encounters | `gba_gen3_wild_land` | D6's rate mapping for every method; caves and forest |
| Trainers | `gba_gen3_trainers` | Route and gym trainers; items in parties (refused today); trainer classes |
| Gym and badge | 3a/3b's scripts | Badge flags, the TM reward, the gym's scripts |
| Items, TMs, Marts | Item extraction (above) | FireRed's Mart lists; TM contents by Q9 |
| Checks | Step B's harness | Routes through the slice; a save and load in the harness; then on hardware (D13) |

Phase 3.5's exit needs a device (E7, Q4) and the fidelity of the slice classified against `01-feasibility.md`. The
release channel (D14) and GPL source tagging (R-07) are decided before anything is published.

## Risks

- **The harness costs more than it saves.** Mitigation: state-based waits from the start, routes kept short, and
  manual play still allowed for any row.
- **Generated maps stay "a bit off".** Step C is small on purpose. If D11 still says no after it, the matrix waits and
  the story stays on the stand-ins, which play.
- **Runtime bugs hidden under build-level checks.** Patches `0006` to `0010` change game code in ARM9 main or overlays,
  and none of their effects has been seen in game. Step B's first routes look for exactly that.

## Not in this plan

- Phase 4 and later: the rest of Kanto, LeafGreen, Sevii, RBY.
- New art for the player, Oak or buildings (D3, D4).
- Species expansion and forms.
