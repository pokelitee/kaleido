# content

Game content, as layers over the engine's `res/` and `generated/` (`docs/plan/03-architecture.md` §5 and §6):

```
regions/kanto/            shared geography
families/frlg/            one story: maps, NPCs, events, scripts
games/firered/            one ROM: game.json, title, save magic, B2W2-system switches
```

A layer holds `layer.json`, `provenance.json`, `generated/` (constant additions), `res/` (files at upstream's paths)
and `extract/` (extraction recipes, never extracted data).

- Every committed file has exactly one provenance category. Here that is `original` (licensed CC BY-SA 4.0,
  [`LICENSE-CONTENT`](../LICENSE-CONTENT)) or `third-party` (with its recorded license).
- Black 2/White 2 data comes from the engine. Other games' content is extracted on the builder's machine from their
  own ROMs and is never committed: only the recipe that extracts it.

Phase 1 adds the `firered` game with a tiny test layer: E1's text change, a reused zone (ADR 0004), and E8's encounter
table.
