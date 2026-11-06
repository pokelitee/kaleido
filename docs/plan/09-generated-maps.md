# 09 — Plan: Kanto's maps generated from FireRed

Status: **proposed** (2026-11-06), for ADR 0006 (D10 in `08-phase3.md`). It replaces Phase 3's step 5 (W6, map art)
and changes how the story's maps are laid out. It estimates sizes, not time.

## Goal

Every Kanto map built on the player's machine from their FireRed:
- **the layout**, from FireRed's map grid;
- **the look**, from Black 2's textures and props, by ADR 0003's template-append;
- **collision and heights**, from FireRed's collision and elevation;
- **events, warps and people**, at FireRed's own positions.

Any map stays replaceable by a hand-made model in a layer.

Phase 3's exit becomes: the story plays from New Game to the Parcel on generated Pallet Town, Route 1 and Viridian
City, and the converter's cost and the touch-ups per map are recorded.

## What each side has

**FireRed** (pret/pokefirered at `ce6406d8`, read for formats; nothing copied):
- **The layout:** a map's header points to its layout: width, height, a border block, and a grid of 16-bit cells.
  Each cell holds a metatile (bits 0–9), a collision value (10–11) and an elevation (12–15).
- **Tilesets:** a layout names a primary and a secondary tileset. Each metatile has graphics and an attribute word:
  its behavior (about 110 kinds, such as tall grass, water, ledges, doors and counters), terrain, encounter type and
  layer.
- **Connections:** maps join their neighbors at an edge and an offset.

**Gen 5** (pokebw2 at the pin):
- **Zones:** a zone names a map matrix and an area. A matrix is a grid of chunks, each a map model; the overworld's
  also has a zone per chunk. An area names a texture set, a prop bundle and lights.
- **Chunks:** each chunk is 32×32 tiles: `model.glb`, `terrain_0.csv` (each tile's shape, slope, height and tile
  type) and props placed as empties in the GLB. Each chunk has a size budget of 86,020 bytes for most map types (E4b).
- **New chunks** come in by template-append (ADR 0003, engine patch to come): new geometry and collision with a
  template's materials. Areas are capped at 409, so generated maps reuse existing areas' texture sets and props.

## The converter

1. **Read** each map from the ROM: layout, grid, the tilesets' metatile behaviors, connections and events. It goes by
   group and number, as the dialogue extractor does.
2. **Classify** every tile into a kind: grass, tall grass, path, water, ledge (and its direction), tree, building,
   door, fence, flowers, wall and so on.
   - Behaviors give some kinds directly: tall grass, water, ledges, doors.
   - Others share a behavior and differ only in their graphics, such as tree, roof and fence, which all block. For
     those, a committed label table gives each metatile of a tileset its kind: Kaleido's own labels, made once per
     tileset with a tool that shows each metatile on the builder's machine.
3. **Lay out** the maps on a grid of 32-tile chunks, as FireRed's connections join them. Each map's tiles keep
   FireRed's coordinates, offset to its place in the matrix, and the edge of the matrix is filled with the map's
   border block.
4. **Build** each chunk:
   - ground as textured quads, merged by kind to stay under the chunk budget;
   - trees, fences and other repeated objects as props of the area's bundle;
   - buildings as the nearest Black 2 house, copied from an existing chunk to fit the footprint;
   - its terrain CSV from collision, elevation and kind (tall grass, water, ledges, doors).
5. **Map Gen 5's tile types** from FireRed's behaviors, in a table proven against Black 2's own chunks: encounters in
   tall grass, surfing, ledges that jump, door warps.
6. **Place events** at FireRed's positions in the matrix: people, signs, warps and triggers, extracted as dialogue
   is. The stand-ins' hand-placed events and the scripts' positions move to FireRed's coordinates.
7. **Let any map be replaced.** A layer's `res/field/maps/models/<map>/` for a map replaces the generated one, and
   its events stay where they are.

## Order

1. **Template-append**, the engine patch E4b prototyped (ADR 0003), with a check of each chunk against its budget.
2. **The spike: Pallet Town on its own.** One FireRed map of 24×20 tiles, one chunk.
   - Its ground, trees and building blocks, collision and tall grass.
   - It is placed for its zone and walked through with Black 2's camera and lights.
   - It proves the classification, the tile types, the budget and template-append, and records the converter's cost.
   - **This is the check before the rest of the plan:** the owner plays it and judges the look.
3. **The Kanto matrix:** Pallet Town, Route 1 and Viridian City joined, with their zones and FireRed's events, warps
   and people. The story's scripts move from the stand-ins to FireRed's coordinates.
4. **Interiors:** the houses, the lab, the Mart and the Pokémon Center, generated the same way. Black 2's generic
   Pokémon Center and Mart are a fallback where they fit better.
5. **Phase 3's exit** on generated maps; then Phase 3.5's maps the same way.

Each step lands as its own pull requests, validated and built.

## Unknowns, settled by the spike or before it

| Unknown | Why it matters | How it's settled |
| --- | --- | --- |
| Gen 5's tile types for tall grass, water, ledges and doors | Encounters, surfing, jumps and warps depend on them | Read the field code and Black 2's own chunks |
| A chunk of quads against the 86,020-byte budget | A tile per quad may not fit | Merge quads by kind; measure the spike |
| Buildings | FireRed draws them from metatiles, Gen 5 builds them as 3D | First blocks, then copies of Black 2's houses |
| A second matrix with its own zones | Kanto's overworld beside Unova's | Read the matrix loader; else Kanto's chunks go into an unused corner of the overworld matrix |
| FireRed's elevations as Gen 5 heights | Ledges, bridges and stairs | Start flat except ledges; heights where a map needs them |
| The look | Kanto in Unova's pieces, top-down layouts under a 3D camera | The owner's playtest of the spike |

## Risks

- **R-01, art.** This plan trades the artist's time for a converter. If the look falls short, a hand-made model can
  still replace any map, as ADR 0006 keeps.
- **R-05, RAM.** Generated chunks are no larger than Black 2's, within the same budget.
- **The stand-in work.** It moves rather than being lost: the extracted dialogue, the trainers and the scripts'
  logic stay. Only positions change.
