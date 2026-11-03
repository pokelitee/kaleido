# Architecture

The architecture as it exists now. The full design is in `docs/plan/03-architecture.md`; this file tracks what is
decided and what is built.

## Built

Nothing yet: the repository holds documentation only. Phase 1 (`docs/plan/05-roadmap.md`) builds the skeleton.

## Decided

| Decision | Record |
| --- | --- |
| Architecture decisions are ADRs in `docs/decisions/` | ADR 0001 |
| pokebw2 is a git submodule pointing at upstream, pinned to one commit; Kaleido's engine changes are a patch series in `engine/patches/`, each behind a `KALEIDO_*` define; with every define off the engine rebuilds Black 2 byte for byte | ADR 0002 |
| New map art: map models and texture sets are appended from a template (upstream packers extended, offered upstream) through Phase 3; a glTF → Nitro encoder is built before Phase 4; each chunk must fit its map type's `chunkBufferSize` | ADR 0003 |
| Patches carry the extracted content they add (one xdelta per game against the B2 ROM) | `07-open-questions.md`, Q1 |
| Every build fits DS mode (4 MB, DS Lite); DSi mode is never required | Q4 |
| Every game uses Gen 5 mechanics and B2W2's move data. Gen 5 decides how things work (battle and field rules, move data, species stats, types, abilities); the original game decides what is in it (story, dialogue, maps, trainers, encounters, items, learnsets, TM contents). No ruleset mechanism until a game needs a variant | Q6, Q9 (replace the brief's rulesets, Sections 4–5) |
| B2W2-only systems are per-game compile-time switches chosen in each game's config | Q7 |
| Original art and data are CC BY-SA 4.0; engine changes and tooling are GPL-3.0 | Q8; brief |
| Generic engine and tool work is offered upstream | Q10 |
