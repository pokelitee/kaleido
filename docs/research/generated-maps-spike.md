# The generated-maps spike: Pallet Town

Step 2 of `docs/plan/09-generated-maps.md`: Pallet Town generated on its own from the builder's FireRed, for the owner
to play and judge. This file records what the converter rests on. Evidence is pokebw2 at the pin (`41f42ca`) with
Kaleido's series, the owner's FireRed (SHA1-checked) and pret/pokefirered at `ce6406d8`, read for formats only.
Images rendered from the ROM stayed in a scratch directory.

## 1. A Gen 5 chunk

**Verified** in pokebw2's sources and `docs/data.md` ("Map model sources"):
- A chunk's directory holds `model.glb`, `terrain_0.csv`, `terrain_0_splits.csv` and `data.json`.
- **Geometry:** the GLB has one mesh whose primitives are the Nitro model's draw calls, one material each. They share
  one vertex pool with positions, UVs, white vertex colors, normals and a one-joint skin. The packer can re-encode a
  primitive's triangles freely (`rebuild_topology`), but the draw calls and material slots must stay the template's:
  adding either isn't supported. A primitive needs at least one triangle.
- **Units:** a tile is 16 units, and a chunk's 32×32 tiles span −256 to 256 on x and z. Tile (x, z) of the chunk is
  x·16 − 256 to (x+1)·16 − 256, and likewise on z.
- **Size of re-encoded geometry:** each triangle's three vertices are written out in full, with a color, a normal, a
  UV and a position: 36 bytes a vertex, about 216 bytes a tile-sized quad. The new display lists are appended after
  the template's old ones, which stay in the chunk. So a chunk of one quad per tile (≈172 KB for 1,024 tiles) can't
  fit, and same-kind tiles must merge into large quads whose texture repeats.
- **Props** are scene-root empties named `bw2_prop_NNNN_id_XXXXX`, translation and a Y rotation only, where the ID
  is the prop's `res_id` in the area's prop bundle (`res/field/props/exterior/models/<bundle>/*/data.json`).
- **Collision** (`terrain_0.csv`) is a row per tile: shape, slope index, height index (`offset`) and `tile_type`.
  The tile type is `(flags << 16) | class` (`GetTileFlags`, `GetTileClass` in `src/ov036/map_attr.c`). Flags:
  `0x1` collision, `0x2` water, `0x4` wild encounters, `0x40` reflection (`include/field/field_map.h`).
- **Heights:** a flat tile's height is minus its entry in `MAP_HEIGHT_OFFSET_TABLE`
  (`src/ov036/field_map_chunk_height.c`): index 51 is y = 16, the ground; index 169 is y = 8, a pond's surface.

**Verified**: the tile types Black 2's 1,065 chunks use, by kind, the most common of each:

| Kind | Class | Flags | Tile type | Tiles |
| --- | --- | --- | --- | --- |
| Walkable ground | `0x00` | `0x80` | `0x800000` | 124,303 |
| Blocked | `0x01` | `0x81` | `0x810001` | 730,501 |
| Tall grass (single battles) | `0x04` | `0x24` | `0x240004` | 6,494 |
| Water to surf | `0x3f` | `0x16` | `0x16003f` | 16,233 |
| Shore, where surfing starts | `0x41` | `0xc3` | `0xc30041` | 2,062 |
| Ledge, jumping down | `0x75` | `0x01` | `0x10075` | 221 |

## 2. The template and the area

The spike's chunk takes `MAP_MODEL_OVERWORLD_2_MAP02_21` (Route 19, beside Aspertia) as its template. **Verified**:
- It is 38,264 bytes, so with the overworld's 110,600-byte buffer (map type 0) about 72 KB are left for new geometry.
- Its 29 materials cover grass (`grass01ax`), tall grass (`kusa_ec1` to `ec3`), paths (`michi01a`, `michi01b`),
  flowers (`hana01_1`), a pond (`ike01`), trees (`ki02c`, `ki03ax`, `ki03bx`, `ki03dx`), a fence (`saku01a`), shore and
  cliffs.
- Their UV densities, in texture repeats a tile: grass 0.25, paths, flowers and tall grass 1, the pond 0.5.
- Heights: ground at y = 16, flowers at 18, tall grass in three layers at 18, 22 and 24, the pond at 8.
- A tree is 20 triangles on a 2×2-tile base, 3 units above the ground: shadow quads (`ki02c`), canopy quads at +20
  and +43.3 (`ki03bx`, `ki03dx`) and leaning upright planes up to +53 (`ki03ax`).

Pallet Town's stand-in zone is Aspertia City (`ZONE_ASPERTIA_CITY`, cells (1, 22) and (1, 23) of the overworld
matrix). Its area's texture set holds the template's textures (27 of 29 by name; `hana01_1` is `hana01.1` there), so
the area stays as it is. Overworld chunks bind their textures by name to the current zone's set. **Verified** by
comparing the sets' PNGs; **Unverified** in game.

## 3. Buildings and doors

Black 2's buildings are props, not chunk geometry. Aspertia's bundle (`FIELD_PROPS_EXTERIOR_ASPERTIA_CITY`) has two
houses (`c12_house_01`, `res_id` 305; `c12_house_02`, 306), a larger building (`c12_build_01`, 304), signs (151 to
154) and others. **Verified** from Aspertia's chunks and warps:
- Houses sit on tile corners and one-tile props on tile centers.
- The door warp is one tile in front of a house's origin: (x, z + 1) for 305, (x − 1, z + 1) for 304.
- No door props are placed in chunks.

So a FireRed building becomes a house prop placed with its door on FireRed's door tile, which keeps the warp, and
everything around it, on FireRed's grid. Black 2's houses are about 5.5 by 5 tiles; FireRed's are 5 by 4.

## 4. FireRed's side

**Verified** in pret (read for formats) and on the ROM:
- A map header's first word points to its layout: width, height, border, grid, the primary and secondary tilesets,
  and the border's size.
- A grid cell is a metatile (bits 0–9), collision (10–11) and elevation (12–15).
- A tileset holds its tiles (the primary's LZ77-compressed), palettes, metatiles (eight tile entries, two layers) and
  a 32-bit attribute per metatile: behavior in bits 0–8, layer type in 29–30. The primary has metatiles 0 to 639.
- Pallet Town (map 3.0) is 24×20 on the General and Pallet Town tilesets, with a 2×2 border of trees. It uses about
  100 metatiles. Behaviors mark the water (`0x15`), the doors (`0x69`) and the signs and mailboxes (`0x84`); trees,
  roofs, walls, fences, flowers, paths and grass all share the normal behavior, so a label table tells them apart.

## 5. The converter

`framework/kaleido/mapgen.py`, run by the recipe kind `gba_gen3_map_model` (`framework/kaleido/extract.py`). It reads
the layout with `framework/extractors/gba_gen3_layout.py`, gives each tile its kind from the labels, and places the
map at its origin in a 32×32 chunk:
- **Ground:** the tiles of each surface (grass, path, water, flowers) merge into rectangles, a quad each. Its texture
  repeats at the template's density, on the chunk's coordinates, so neighboring quads meet. Flowers are a second quad
  2 units up; water is at y = 8, with banks facing it. A fence run is the template's two flat strips.
- **Trees:** each 2×2 group of tree tiles gets a copy of the template's tree, 20 triangles. A one-wide pair gets one
  half a tile out. **Verified** against the template's collision: a tree's base is the two rows starting one tile
  past its first upright plane, and its canopy leans back over the two rows behind, as Black 2's trees do.
- **Props:** each building's prop stands with its door on FireRed's door tile; signs and mailboxes on their tiles.
- **Collision:** FireRed's, with water's edge tiles as shore and the rest as water to surf. A building's body blocks
  the tiles it covers up to its door's row, since Black 2's buildings aren't FireRed's shapes, but never the tile in
  front of a door.
- **Outside the map:** blocked grass, and the map's edge water runs on to the chunk's edge.
- A material the map doesn't use keeps one degenerate triangle, since a draw call needs one.

## 6. The spike's results

**Verified** on the owner's machine (2026-11-06):
- **Size:** Pallet Town is 672 triangles (580 of them its 29 trees) and 8 props. The chunk packs to 80,568 bytes,
  under the overworld's 110,600. Without patch `0012` it was 113,256 bytes, 2,656 over.
- **Patch `0012`:** the packer wrote a color and a normal with every vertex. Writing them only when they change (a
  normal after any color, since with lighting on the normal's lit color replaces it) draws the same and takes 20
  bytes a vertex instead of 36.
- **Time:** generating takes about 2 seconds, and packing the model archive about 3 minutes of the build.
- **The spike game builds** (`firered_spike`): validation clean, every chunk within its budget, its patch applies.
- **Cost of the tooling:**
  - the converter, about 530 lines;
  - the layout reader, 100;
  - the recipe kind, 80;
  - two engine patches;
  - tests on synthetic data.
- **Cost of the data:**
  - Labels go per tileset: about 100 metatiles for Pallet Town, read off a sheet of them that the builder's machine
    draws. The primary tileset's labels serve every map.
  - A kit goes per template: one JSON file, measured from the template.
  - A recipe goes per map: its origin and its buildings.

**Touch-ups the spike found**, for the owner's playtest and step 3:
- **Buildings:** with their doors on FireRed's, Black 2's houses reach about a tile left of FireRed's (over the
  mailboxes), and the lab stands about two tiles right and reaches two rows deeper.
- **Outside the map:** plain blocked grass. FireRed shows its border trees there.
- **The bottom edge:** the tree tops along it (Route 21's trees) are drawn as grass.
- **Stand-ins:**
  - mailboxes use a small sign prop;
  - signs can't be read, since the spike has no events;
  - the map's name is Aspertia City's.

**Unverified:** how all of it looks and plays in game. That is the owner's playtest of the spike ROM.
