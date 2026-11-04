# content

Game content, as layers over the engine's `res/` and `generated/` (`docs/plan/03-architecture.md` §5 and §6):

```
regions/kanto/            shared geography; zones.json maps its locations to existing zones (ADR 0004)
families/frlg/            one story: maps, NPCs, events, scripts, extraction recipes
games/firered/            one ROM: game.json, its own text, save magic, B2W2-system switches
```

## A layer

| File | What |
| --- | --- |
| `layer.json` | `{"kind": "region" \| "family" \| "game"}`, matching its directory |
| `provenance.json` | `{"entries": [{"paths": [patterns], "category": …}]}`: every file under `res/` and `generated/` matches exactly one entry. `original` content is CC BY-SA 4.0 ([`LICENSE-CONTENT`](../LICENSE-CONTENT)); `third-party` entries add `license`, `author` and `source`; `extracted` entries name their `recipe` and are never committed |
| `res/`, `generated/` | content at upstream's paths. `res/P` replaces upstream's file; `res/P.merge.json` patches it (RFC 7396 for JSON; message labels and their text for `res/text/`); `generated/<list>.txt` appends constants |
| `extract/<name>.json` | a recipe: what to read from the player's source ROM (`kaleido extract`). The output lands in `build/<game>/extracted/`, never in git |
| `zones.json` (regions) | `{"locations": {"route_1": "ZONE_ROUTE_19"}}`: which existing zone holds each location |

Black 2/White 2 data comes from the engine. A layer never commits a copy of upstream's files: it patches them, or
replaces them with its own.

## Games

`games/<game>/game.json` names the game, its layers (lowest first), the source ROMs its recipes read, and the
`KALEIDO_*` defines it builds with, all strings (`""` for a define without a value). `./kaleido build <game>` reads it.

- Every game has its own `KALEIDO_SAVE_MAGIC` (E9). It is never Black 2's two magics, 0 or 0xffffffff, nor another
  game's, and it never changes once a release is out: a game with a new magic finds no saves.
- `firered`'s is `0x4b465231` ("KFR1").

## FireRed's test layers (Phase 1)

| Layer | What |
| --- | --- |
| `regions/kanto` | `route_1` lives in `ZONE_ROUTE_19`, Aspertia's first route, for now |
| `families/frlg` | `extract/route_1_encounters.json`: FireRed's Route 1 land encounters, into that zone's encounter table |
| `games/firered` | Professor Juniper's first line replaced with original text, as E1 did |

Phase 3 replaces these with real Kanto content.
