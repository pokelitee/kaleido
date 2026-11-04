# content

Game content, as layers over the engine's `res/` and `generated/` (`docs/plan/03-architecture.md` §5 and §6):

```
regions/kanto/            shared geography; zones.json maps its locations to existing zones (ADR 0004)
families/frlg/, rby/      one story each: maps, NPCs, events, scripts, extraction recipes
games/firered/, red/      one ROM each: game.json, its own text, save magic, B2W2-system switches
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
`KALEIDO_*` defines it builds with, all strings (`""` for a define without a value). Its `title`, a list of up to three
lines, is what the DS menu shows; without one the ROM keeps Black 2's. Its `start` names the location a new game starts
in, as the region's `zones.json` does; `build` turns it into `KALEIDO_NEW_GAME_ZONE` (patch `0007`), and a game names
one or the other. `./kaleido build <game>` reads it.

- Every game has its own `KALEIDO_SAVE_MAGIC` (E9). It is never Black 2's two magics, 0 or 0xffffffff, nor another
  game's, and it never changes once a release is out: a game with a new magic finds no saves.
- `firered`'s is `0x4b465231` ("KFR1"); `red`'s is `0x4b524431` ("KRD1").

## Test layers (Phases 1 and 2)

| Layer | What |
| --- | --- |
| `regions/kanto` | Phase 3's stand-ins (`docs/plan/08-phase3.md`, D1): nine Kanto locations on Unova zones in `zones.json`. Pallet Town is on Aspertia City, Route 1 on Route 19 and Viridian City on Floccesy Town, which Unova's maps already join. Each stand-in, and Aspertia's gate to Route 19, loses Black 2's NPCs, triggers, signs and map scripts and keeps its warps. FireRed and Red share it |
| `families/frlg` | `extract/route_1_encounters.json`: FireRed's Route 1 land encounters, into that zone's encounter table |
| `games/firered` | Professor Juniper's first line replaced with original text, as E1 did |
| `families/rby` | Juniper's second line replaced with original text, so the family layer shows under the game's |
| `games/red` | A stub with no source ROM: Juniper's first line replaced with original text, and no C-Gear (`KALEIDO_NO_CGEAR`) |

Phase 3 replaces these with real Kanto content.
