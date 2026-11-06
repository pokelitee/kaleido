# 0006. Generate Kanto's maps from the source game, with Black 2's art

- Status: Accepted (by the owner, 2026-11-06)
- Date: 2026-11-06

## Context

Kanto needs about 425 maps (`05-roadmap.md`, "Workload"). Phase 3's plan put Kanto's story on Unova stand-in maps
first, then rebuilt Pallet Town (and Route 1) by hand to measure the cost of new art (D1, D2 in `08-phase3.md`). Hand
art at that scale needs an artist for every map, which is the project's largest cost (R-01).

ADR 0003's template-append adds new map models that keep an existing model's materials and textures: new layouts,
geometry, collision and props, but Black 2's look (`docs/research/e4b-map-art.md`). FireRed's own maps are data in
the player's ROM: each layout a grid of metatiles, with collision and elevation per tile, and behaviors per metatile
(pret's formats, read for behavior).

## Options

1. **Hand-made art** (D1, D2): the best look, an artist's time per map.
2. **Hand kit-bash**: each map rebuilt in Blender from Black 2's textures, props and buildings. No new art, but
   modeling time per map.
3. **Generated from the source game**: a converter reads each map's layout from the player's ROM at build time and
   builds Gen 5 maps from Black 2's pieces by a mapping of tile kinds. One tooling effort, then touch-ups per map; a
   rougher look.

## Decision

Option 3 (D10 in `08-phase3.md`). Kanto's maps are built from the source game's layouts, with Black 2's textures and
props, by template-append. Each map stays replaceable:
- **FireRed's own grid.** Maps keep it, one tile to one tile, so events, warps and people take FireRed's positions
  and stay right under any art.
- **A per-map override.** A map's generated model is a default: a hand-made model in a layer replaces it, by the
  usual layer rules.
- **One mapping for every map.** The mapping from FireRed's tile kinds to Gen 5 pieces is one data file.

## Consequences

- **Generated maps are extracted content,** built on the player's machine and never committed, as text and tables
  are. The mapping and the converter are Kaleido's own (original, GPL-3.0 for the code).
- **The stand-ins go away** as generated maps replace them. Their scripts' positions change to FireRed's coordinates.
- **Phase 3's art-cost exit** measures the converter and the touch-ups per map, not hand art.
- **The look is Approximate:** Kanto drawn with Unova's pieces. Hand art for any map stays possible later.
- **New things to prove** (`docs/plan/09-generated-maps.md`): Gen 5's tile types for FireRed's behaviors; a chunk's
  size budget; buildings; heights; a Kanto map matrix with its own zones.
