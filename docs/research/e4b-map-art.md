# E4b — New map art

Phase 0 experiment (`docs/plan/05-roadmap.md`), run 2026-11-03 on the owner's machine in the scratch checkout
`~/kaleido-work/pokebw2` at pokebw2 `41f42ca1afe6291f00b0ba0ec3f6099b9ff1346c`. Question: can new map models and texture
sets get into the ROM, which Gen 5-style Kanto needs (R-01)? And if not as things stand, what does it take?

## Summary

- **As upstream stands, no.** Adding a map model or a texture set stops the build. **Verified**.
- **A ~25-line change to upstream's two packers makes it possible** for entries that start from an existing one (a
  "template"). A test ROM with a new map model (#1065) and a new texture set (#409) builds, the original entries stay
  byte-identical, and the DSi digests check out. **Verified** structurally, and in game: the owner ran it in melonDS
  and it played like normal Black 2.
- **The engine has room for more**: map chunk IDs are `u32`, texture set IDs `u16`. Area records are capped at 409
  by a constant (`AREA_COUNT`). **Verified** in source.
- **Every map chunk has a hard size budget**: the map type's `chunkBufferSize`, 86,020 bytes for most types.
  **Verified** in source.
- **Recoloring a whole texture set can fail**, because textures share encoded data that the packer can't re-encode
  independently. **Verified** (failed twice).
- Template-appending covers new layouts, geometry, UVs, terrain, props and material colors. It doesn't cover new
  materials, draw calls, texture names, sizes or formats; those need a real Nitro encoder. That fits the Q3 direction:
  template-append for the prototype phases, then an encoder before Phase 4.

## 1. What upstream does today

Adding a constant and a directory (a copy of an existing one) and running each packer:

```
ValueError: a/0/0/8 has 1065 map models and map_models.txt 1066
ValueError: a/0/1/4 has 409 texture sets and its list 410
```

Both packers patch each entry onto the extracted original (`pack()` in `tools/data/map_model_data.py` and
`tools/data/map_texture_data.py`), so the count must equal the original archive's. **Verified**.

## 2. Engine limits on new entries

All **Verified** in pokebw2's source at the pin:

| Reference | Width or limit | Where |
| --- | --- | --- |
| Map chunk ID in a matrix cell | `u32`, up to 900 cells per matrix (`chunkIds[900]`) | `include/field/field_map.h`, `MapMatrix` |
| Texture set ID in an area record | `u16` (`texSetId`) | `include/system/area_data.h`, `AreaData` |
| Area records | **409**: IDs at or above `AREA_COUNT` (0x199) silently read record 0 | `src/system/area_data.c` |
| Chunk size | `chunkBufferSize` per map type: 0x15004 (86,020 B) for most, 0x1b008 (110,600 B) for some, 0x54010 (344,080 B) for one | `src/ov036/fieldmap.c`, `MAP_CONFIGS` |
| Field heap per map type | 0x136800 (1,271,808 B) for most; 0x12a000 and 0xaa000 for two | same |
| Chunk archive | `chunkArcId` 8 (`a/0/0/8`) in every map type | same |

Searches for the literal counts (1065/0x429, 409/0x199) found no other hard-coded limit. `AREA_COUNT` is the one
literal 409; the other matches are unrelated (message file 409, a heap line number). **Verified** by grep, which is
not proof that no derived limit exists elsewhere.

What the original data uses (`extract/b2_us/files`), **Verified** by measurement:

| Archive | Count | Median | 95th percentile | Max | Over 86,020 B |
| --- | --- | --- | --- | --- | --- |
| Map chunks `a/0/0/8` | 1,065 (961 WB, 60 GC, 36 NG, 8 RD) | 27,240 B | 57,192 B | 99,884 B | 4 |
| Map texture sets `a/0/1/4` | 409 | 49,416 B | 77,416 B | 170,928 B | — |

So the budget Kanto chunks must meet is the real one B2W2 already works within: most chunks are well under 86,020
bytes, and only a few use the larger buffers.

Consequences:

- New chunks and texture sets can be referenced; nothing in the formats stops IDs past the originals.
- New *areas* past 409 need a one-line engine change (raise `AREA_COUNT`, a `KALEIDO_` define), or reuse of existing
  records. `docs/data.md` counts 81 records that nothing names, and Unova's records are free in a Kanto game.
- The validator must check each chunk's size against its zone's map type (R-22).

## 3. The template-append prototype

Change (25 lines added, 8 removed, plus one schema property), recorded as
[`e4b-template-append.patch`](e4b-template-append.patch). It applies cleanly to the pin (`git apply --check`):

- `map_model_data.py`: a model directory past the original count must name a `template` (a `MAP_MODEL_` constant) in
  its `data.json`. The packer starts from that model's original chunk, appends it, then applies the GLB, terrain and
  prop edits as it does for any model.
- `map_texture_data.py`: a texture set directory past the original count names its template in `template.json`. The
  packer encodes the folder's PNGs onto the template set and appends the result.
- `map_model.schema.json`: allows `template`.

Test content, on a scratch branch only:

- `MAP_MODEL_KALEIDO_E4B_MODEL` (#1065): a copy of `OVERWORLD_2_MAP01_22`, one of Aspertia City's two overworld chunks,
  placed in its cell (22, 1) of `MAP_MATRIX_OVERWORLD`.
- `MAP_TEXTURE_SET_KALEIDO_E4B_SET` (#409): a copy of Aspertia's texture set, named by Aspertia's four seasonal area
  records.

Built with `ninja build/pokeblack2_us.nds`. That target skips the per-archive matching checks, which a changed ROM
must fail. Results, **Verified**:

| Check | Result |
| --- | --- |
| Build | succeeded (194 s incremental) |
| `a/0/0/8` | 1,066 entries; all 1,065 originals byte-identical; #1065 equals its template's bytes |
| `a/0/1/4` | 410 entries; all 409 originals byte-identical; #409 equals Aspertia's set (65,712 B) |
| Overworld matrix cell (22, 1) | chunk ID 1065 |
| Area records naming set 409 | 4 (Aspertia's seasons) |
| DSi digests and HMACs (`tools/build/verify_dsi_rom.py`) | all OK, "dump is intact" |
| ROM | SHA1 `09d7213d3b474d2e2a144247e6e5d05cb4bd30a9`; header used size `0x118ec400` (~282 MiB of 512 MiB, with the DSi area) |

**In-game check, passed (2026-11-03)**: the owner ran the test ROM (`~/kaleido-work/e4b/kaleido-e4b-test.nds`, never
committed) in melonDS, and it "runs like normal Black 2". The game starts in Aspertia City, where cell (22, 1) loads
chunk #1065 and every area record loads set #409. If appended IDs had failed, that cell would be empty or untextured,
or the game would crash there. The copies are identical to their templates, so this proves the IDs load. It doesn't
prove anything about edited geometry or textures, which the Phase 3 prototype will exercise. Not checked: DSi mode
and hardware (E7).

### The recolor that failed

To make the test visible, the first version swapped red and blue in every PNG of the new set. The packer refused:

```
ValueError: texture set 409/gake1_1: shared Nitro data cannot represent the edited PNGs together
```

A second attempt recolored only the 112 of 120 textures that, by our reading of the BTX0 tables, share no texels or
palette with another texture. It failed on the same texture. The packer's idea of shared data is wider than our
reading, and we stopped there (the owner's two-failures rule). What this means:

- Recoloring existing textures is not freely possible: the packer can only re-encode edits that its shared texel and
  palette layout can still represent.
- New Kanto textures should not be made by recoloring Unova's within a template set. They need either new textures in
  new sets, which only an encoder can create, or editing that respects the sharing.

## 4. Routes for Kanto's map art

| Route | What it allows | What it doesn't | Cost |
| --- | --- | --- | --- |
| Repurpose (overwrite Unova entries) | Same as edits to existing entries | Overwritten Unova entries are lost; otherwise the same limits as template-append | None (works today) |
| **Template-append** (this prototype) | New entries alongside Unova's: new layouts in matrices, new geometry and UVs (triangles re-encoded), terrain, props, material colors, rebinding to textures in the same set | New material slots or draw calls; textures beyond the template set's names, sizes and formats; arbitrary recolors | Done as a prototype (~25 lines); upstreamable |
| **Nitro encoder** | Any glTF material and texture layout: new BMD0 models and BTX0 sets from scratch | — | Large, see below |

What an encoder has to add on top of upstream's existing code. Upstream already has GPU command encoding of triangles,
material color packing, texel and palette encoding for known formats, terrain and prop sections, NARC and Nitro
dictionary writers:

1. A BMD0 writer: model header, node tree, material table, one shape and display list per material, bounding box and
   scale.
2. A BTX0 writer: texture and palette dictionaries, a format choice per texture, palette quantization for new PNGs.
3. New chunk containers (WB/GC/NG/RD headers around model, terrain and props).
4. Validation: chunk size against `chunkBufferSize`, texture memory, DS GPU per-frame limits (R-22).

**Assumption** on size: roughly comparable to upstream's two existing packers together (`map_model_data.py` 1,281
lines plus `map_texture_data.py` 413 lines), plus verification in melonDS and a viewer such as Apicula. Not
estimated in time; the Phase 3 prototype will measure what template-append can't do, which sets the encoder's real
scope.

## 5. Recommendation

Proposed in [ADR 0003](../decisions/0003-new-map-art.md):

1. Kaleido's engine patch series takes template-append (offered upstream first, per Q10) for Phases 1–3. Unova
   entries stay untouched.
2. A `KALEIDO_` define raises `AREA_COUNT` when Kanto needs more areas than the free records.
3. The Nitro encoder is built before Phase 4, scoped by what the Phase 3 prototype couldn't do.
4. The validator enforces the chunk size budget per map type.

## Risks this touches

- R-01 (new map art): partly retired. New entries are possible; full material and texture freedom still needs the
  encoder.
- R-17 (engine capacity): `AREA_COUNT` 409 found; IDs for chunks and texture sets are wide enough.
- R-22 (rendering budget): chunk buffer sizes found; texture memory and GPU limits still open.
