# 0003. Add new map art by template-append, then a Nitro encoder

- Status: Proposed
- Date: 2026-11-03

## Context

Gen 5-style Kanto needs hundreds of new map chunks and new texture sets (R-01). E4b (`docs/research/e4b-map-art.md`)
found, at pokebw2 `41f42ca`:

- Upstream's packers refuse any map model or texture set the original archives don't have.
- A ~25-line change lets a new entry start from an existing one (a template) and be appended. A test ROM with a new
  chunk (#1065) and texture set (#409) builds with all originals byte-identical and valid DSi digests. The in-game
  check is pending.
- The engine addresses chunks with `u32` and texture sets with `u16` IDs. Area records are capped at 409
  (`AREA_COUNT`). Each chunk must fit its map type's `chunkBufferSize` (86,020 bytes for most types).
- An entry built from a template keeps the template's material slots, draw calls, texture names, sizes and formats.
  Recolors of shared texture data can be refused.

The owner chose the direction in Q3: repurpose or reuse Unova structure for the prototype, then an encoder before
Phase 4.

## Options

1. **Repurpose only**: overwrite Unova chunks and sets. No tooling, but Unova data is lost and every limit of
   template-append applies.
2. **Template-append now, encoder later**: new entries alongside Unova's from Phase 1; a real glTF → Nitro encoder
   (BMD0 and BTX0 writers) before Phase 4, scoped by what Phase 3 couldn't do.
3. **Encoder first**: the most freedom, but Phase 3 waits for the largest Tier 1 tooling task.

## Decision (proposed)

Option 2.

- Engine patch: template-append in the map model and texture set packers, as recorded in
  `docs/research/e4b-template-append.patch`, offered upstream first (Q10).
- Engine patch: a `KALEIDO_` define that raises `AREA_COUNT` when Kanto needs more areas than the free records allow.
- Framework validation: each chunk's size against its zone's map type `chunkBufferSize`.
- The encoder is planned as a Phase 3.5 to Phase 4 workstream, with its scope written down at the end of Phase 3.

## Consequences

- Kanto's prototype art is shaped by B2W2's materials and texture layouts: artists pick templates whose material slots
  fit, and reuse their textures. Visual variety is limited until the encoder exists.
- Unova data stays intact, so the matching baseline and other experiments are unaffected.
- The encoder becomes a scheduled dependency of Phase 4, not an open risk.
- If the in-game check of the E4b ROM fails, this ADR is revisited before it is accepted.
