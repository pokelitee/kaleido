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

## Games

`games/<game>/game.json` names the game and the `KALEIDO_*` defines it builds with, all strings (`""` for a define
without a value). `./kaleido build <game>` reads it.

- Every game has its own `KALEIDO_SAVE_MAGIC` (E9). It is never Black 2's two magics, 0 or 0xffffffff, nor another
  game's, and it never changes once a release is out: a game with a new magic finds no saves.
- `firered`'s is `0x4b465231` ("KFR1").

Phase 1 adds the `firered` layers: a tiny test layer with E1's text change, a reused zone (ADR 0004), and E8's encounter
table.
